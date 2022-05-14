# 6.S081-Lab5: Copy On Write


> There is a saying in computer systems that any systems problem can be solved with a level of indirection.

<!--more-->

lab材料：[https://pdos.csail.mit.edu/6.828/2021/labs/cow.html](https://pdos.csail.mit.edu/6.828/2021/labs/cow.html)

## Implement copy-on write(hard)

> Your task is to implement copy-on-write fork in the xv6 kernel. You are done if your modified kernel executes both the cowtest and usertests programs successfully.

> 实现支持COW机制的fork

lab材料中给的思路已经比较完善了，这个lab的难点在于实现过程中的一些细节，包括何时操作引用数、何时kill当前进程等。

### 背景知识

在RISC V官方手册中可以查到RISC V中的中断号与中断类型。`15`号的写类型中断是我们要处理的中断。

![RISC V中断号](Pasted%20image%2020220513162236.png "RISC V中断号")

当发生页中断时，`stval`寄存器中保存了引起中断的虚拟地址。
![stval寄存器介绍](Pasted%20image%2020220514160856.png "stval寄存器介绍")

在RISC V中，PTE的第8、9位为保留位，可以被用来标记PTE是否是COW类型。
![pte的保留位](Pasted%20image%2020220514161022.png "pte的保留位")


### Solution

这个Lab的实现包含三部分。

#### 记录内存页引用数

很直接的想法就是使用数组来存储每个内存页的引用数，数组长度为`(PHYSTOP-KERNBASE)/PGSIZE`，也就是32768项。并且要注意到，对引用个数的操作需要具有原子性。所以，这里选择将数组直接作为`kmem`全局变量的成员，使用`kmem.lock`来实现原子性。

这个地方的实现过程中有一个比较tricky的点，就是可以将引用数减1的操作直接集成在`kfree()`函数中。即**所有的减少引用数的操作都只会在`kfree()`函数中完成**。 

我一开始还写了个`subrefcnt()`的函数，并且在`kfree()`中也进行了减1操作。结果导致在一些地方我调用了`subrefcnt()`，但是后续过程中还有一些因为进程被kill而产生的隐式`kfree()`调用。这使得引用数被错误地多减了1，从而产生难以排查的错误。

> `kernel/kalloc.c`

```c
// 将引用计数数组加到kmem结构体中，以使用lock
struct
{
    struct spinlock lock;
    struct run *freelist;
    // 记录每个内存页的引用次数
    uint8 pgrefcnts[(PHYSTOP - KERNBASE) / PGSIZE]; // 128*1024*1024 / 4096 = 32768
} kmem;

// 获取pa对应的物理内存页引用次数
// pa需要4096字节对齐
int getrefcnts(void *pa)
{
    if (((uint64)pa % PGSIZE) != 0 || (uint64)pa < KERNBASE || (uint64)pa >= PHYSTOP)
        panic("getrefcnts");
    acquire(&kmem.lock);
    int num = kmem.pgrefcnts[(int)((uint64)pa - KERNBASE) / PGSIZE];
    release(&kmem.lock);
    return num;
}

// 将pa对应的物理内存页引用次数加1
// pa需要4096字节对齐
void addrefcnts(void *pa)
{
    if (((uint64)pa % PGSIZE) != 0 || (uint64)pa < KERNBASE || (uint64)pa >= PHYSTOP)
        panic("addrefcnts");
    acquire(&kmem.lock);
    kmem.pgrefcnts[(int)((uint64)pa - KERNBASE) / PGSIZE]++;
    release(&kmem.lock);
}

void kinit()
{
    // 初始化内存管理器的锁
    initlock(&kmem.lock, "kmem");

    // 首先，将所有的物理内存页的引用次数都设为1
    memset(kmem.pgrefcnts, 1, (PHYSTOP - KERNBASE) / PGSIZE);

    // 然后，对这些内存页调用kfree()，将其加入freelist链表
    freerange(end, (void *)PHYSTOP);
}

void freerange(void *pa_start, void *pa_end)
{
    char *p;
    p = (char *)PGROUNDUP((uint64)pa_start);
    for (; p + PGSIZE <= (char *)pa_end; p += PGSIZE)
        kfree(p);
}

// 将减少引用次数的操作集成在kfree()中
// Free the page of physical memory pointed at by v,
// which normally should have been returned by a
// call to kalloc().  (The exception is when
// initializing the allocator; see kinit above.)
void kfree(void *pa)
{
    if (((uint64)pa % PGSIZE) != 0 || (char *)pa < end || (uint64)pa >= PHYSTOP)
        panic("kfree");

    // 获取锁资源
    acquire(&kmem.lock);

    // 将内存页的引用计数减1
    // 如果引用计数减到了0，那么就将内存页视作空闲的内存页，执行free操作，将其插入空闲页链表
    if (--kmem.pgrefcnts[((uint64)pa - KERNBASE) / PGSIZE] == 0)
    {
        // release(&kmem.lock);
        struct run *r;

        // Fill with junk to catch dangling refs.
        memset(pa, 1, PGSIZE);

        r = (struct run *)pa;

        // 送入freelist链表
        r->next = kmem.freelist;
        kmem.freelist = r;
    }

    // 释放锁资源
    release(&kmem.lock);
}

// Allocate one 4096-byte page of physical memory.
// Returns a pointer that the kernel can use.
// Returns 0 if the memory cannot be allocated.
void *
kalloc(void)
{
    struct run *r;

    acquire(&kmem.lock);
    r = kmem.freelist;
    if (r)
    {
        // 一块内存页被分配的时候，将其引用计数设为1
        kmem.pgrefcnts[((uint64)r - KERNBASE) / PGSIZE] = 1;
        kmem.freelist = r->next;
    }
    release(&kmem.lock);

    // 如果成功分配了一块物理内存页面
    if (r)
        memset((char *)r, 5, PGSIZE); // fill with junk

    return (void *)r;
}
```

#### 修改`uvmcopy()`函数

`uvmcopy()`函数是fork()会调用的函数，实验材料告诉我们应该在该函数中修改原来的页复制逻辑，改为在页表中写入指向相同物理页的COW项。

修改这个函数，需要注意什么时候应该将引用数加1。既然`mappages()`失败会跳转到调用`kfree()`的`uvmunmap()`，所以需要在`mappages()`之前就将引用数加1。

> `kernel/vm.c`

```c
int uvmcopy(pagetable_t old, pagetable_t new, uint64 sz)
{
    pte_t *pte;
    uint64 pa, i;
    uint flags;
    // char *mem;

    // Does va always start from 0?
    for (i = 0; i < sz; i += PGSIZE)
    {
        if ((pte = walk(old, i, 0)) == 0)
            panic("uvmcopy: pte should exist");
        if ((*pte & PTE_V) == 0)
            panic("uvmcopy: page not present");

        // 获取内存页的物理地址
        pa = PTE2PA(*pte);

        // 首先将内存页引用数加1
        addrefcnts((void *)pa);

        // 清除旧页表中PTE项的PTE_W位
        *pte &= (~PTE_W);
        // 将页表项的PTE_COW位置位
        *pte |= PTE_COW;

        // 获取PTE项中的flag信息
        flags = PTE_FLAGS(*pte);

        // 在新的页表中记录同样的内存页物理地址
        if (mappages(new, i, PGSIZE, pa, flags) != 0)
            goto err;
    }
    return 0;

err:
    // 如果出错，那么从new page table中unmap虚拟地址的PTE项，并且执行free操作
    uvmunmap(new, 0, i / PGSIZE, 1);
    return -1;
}
```

#### 实现COW处理逻辑

我们需要在两个地方实现处理COW类型的page fault的代码。一个是`kernel/trap.c`中的`usertrap()`函数部分，另一个是`kernel/vm.c`中的`copyout()`（实验材料中提示了）。

处理的代码实现比较简单，就是申请新的内存页面，然后复制内容并修改pte项。但是如果页面的引用数为1，则直接修改pte项即可。在新的内存页面申请成功之后，对原来的内存页地址执行一次`kfree()`，就可以将其引用数减1。

需要注意的是，`copyout()`函数中可能存在对多个页的写操作，所以处理COW的操作需要写在`while`循环中。还有一个比较坑的点就是，在条件判断的时候需要先对虚拟地址范围做个判断，否则`usertest`测试会超时。

有了上述基础后，可以将判断是否为COW类型pte的功能抽象为一个函数，将处理COW pte的过程抽象为另一个函数。

> `kernel/vm.c`

```c
// 判断是否为COW型pte
int checkCOW(pagetable_t pagetable, uint64 va)
{
    pte_t *pte = walk(pagetable, va, 0);

    // 不是valid page
    if ((*pte & PTE_V) == 0)
        return 0;
    return (*pte & PTE_COW) == PTE_COW;
}

// 处理COW页，返回新分配的物理页地址
void *allocforCOW(pagetable_t pagetable, uint64 va)
{
    pte_t *old_pte;
    uint flags;
    uint64 old_pa, new_pa;

    // 获取pte项
    old_pte = walk(pagetable, va, 0);

    // 获取物理地址
    old_pa = PTE2PA(*old_pte);

    // 如果只有一个进程引用了该物理内存页，那么只需要修改pte项的PTE_W位为1，然后将其PTE_COW位清除即可
    if (getrefcnts((void *)old_pa) == 1)
    {
        *old_pte &= (~PTE_COW);
        *old_pte |= PTE_W;
        return (void *)old_pa;
    }

    // 如果有多个进程的页表引用了该物理内存页
    // 如果内存空间不够，kalloc失败，kill当前进程，并将内存页的引用计数减1
    new_pa = (uint64)kalloc();
    if (new_pa == 0)
        return 0;

    // 将旧的物理内存页面的内容复制到新的物理内存页面中
    // 在这里，已经有了两个物理地址，所以直接调用memmove即可
    memmove((void *)new_pa, (void *)old_pa, PGSIZE);

    // 获取原pte项的flags内容
    flags = PTE_FLAGS(*old_pte);

    // 清除COW位，设置可写
    flags &= (~PTE_COW);
    flags |= PTE_W;

    // 修改pte项
    *old_pte = PA2PTE(new_pa) | flags;

    // 调用kfree()，将old_pa内存页的引用计数减1
    kfree((void *)old_pa);

    // 返回新的物理页地址
    return (void *)new_pa;
}
```

然后在`usertrap()`和`copyout()`中加入这两个函数的调用即可。

> `kernel/trap.c`

```c
void usertrap(void)
{
	...
    else if ((which_dev = devintr()) != 0)
    {
        // ok
    }
    // page fault in RISC V 页中断
    // 0xc: page error caused by instruction fetch
    // 0xd: page error caused by read
    // 0xf: page error caused by write
    else if (r_scause() == 0xf)
    {
        // 获取导致错误的虚拟地址
        uint64 va = r_stval();

        // 以下情况Kill当前进程：
        // 1. 发生错误的虚拟地址超出了进程当前使用的虚拟地址空间范围（如果缺少这个判断，usertest会超时）
        // 2. 发生错误的虚拟地址对应的页不是COW类型
        // 3. COW处理失败

        // 下面的语句因为缺少第一种情况的判断，所以会超时
        // if (checkCOW(p->pagetable, va) == 0 || allocforCOW(p->pagetable, va) == 0)
        if (va > p->sz || checkCOW(p->pagetable, va) == 0 || allocforCOW(p->pagetable, va) == 0)
            p->killed = 1;
    }
    else
    {
        printf("usertrap(): unexpected scause %p pid=%d\n", r_scause(), p->pid);
        printf("            sepc=%p stval=%p\n", r_sepc(), r_stval());
        p->killed = 1;
    }
	...
}
```

> `kernel/vm.c`

```c
int copyout(pagetable_t pagetable, uint64 dstva, char *src, uint64 len)
{
    uint64 n, va0, pa0;

    // 以下操作对每一个页面进行copy操作
    while (len > 0)
    {
        va0 = PGROUNDDOWN(dstva);
        pa0 = walkaddr(pagetable, va0);

        if (pa0 == 0)
            return -1;
        n = PGSIZE - (dstva - va0);
        if (n > len)
            n = len;

        // 对每个dstva目的虚拟地址，都对其进行是否为COW类型的判断
        // 如果是COW类型的pte，则需要为其分配一个新的内存页面，并修改页表中的pte项
        // 再将pa0覆盖为新的内存页地址
        if (checkCOW(pagetable, dstva) && (pa0 = (uint64)allocforCOW(pagetable, dstva)) == 0)
            return -1;

        // 执行copy操作
        memmove((void *)(pa0 + (dstva - va0)), src, n);

        len -= n;
        src += n;
        dstva = va0 + PGSIZE;
    }
    return 0;
}
```

最终通过测试。

![终于过了](Pasted%20image%2020220514151029.png "终于过了")

## 总结
- Lab5是前5个实验中最难的一个
- 每次Debug不要超过2小时（这是我在查资料寻求帮助的时候看到别人记录做这个lab过程中的感想），不然人脑容易宕机
- 最好确保思路清晰再动手写代码，bug解决型编程容易陷入拆东墙补西墙的窘境

## Reference

- RISC-V中各种类型的page fault及处理办法: [https://pdos.csail.mit.edu/6.828/2021/slides/6s081-lec-usingvm.pdf](https://pdos.csail.mit.edu/6.828/2021/slides/6s081-lec-usingvm.pdf)
- 参考的博客一：[https://zhuanlan.zhihu.com/p/463029980](https://zhuanlan.zhihu.com/p/463029980)（感觉这个人的写法过不了usertest）
- 参考的博客二：[https://www.programminghunter.com/article/42462424370/]()（这个应该是可以的）
