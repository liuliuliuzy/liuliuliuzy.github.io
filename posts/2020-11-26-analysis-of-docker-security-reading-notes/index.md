# Analysis Of Docker Security---Reading Notes


一篇关于Docker安全的综述性Paper

<!-- more -->

## 1.文章基本信息
- Title：Analysis Of Docker Security
- Author：[Thanh Bui](thanh.bui@aalto.fi), Aalto University School of Science
- 发布日期：2015.1.13
- 链接：[https://arxiv.org/abs/1501.02967](https://arxiv.org/abs/1501.02967)

## 2.内容概括
这篇文章主要对Docker安全进行了总体上的分析，偏向于资料搜集类型。

文章将Docker的安全分为两个大方面，一方面是Docker自身的安全，也可以看作是Docker各容器之间的安全，分析它们之间是否存在资源未授权访问等问题，另一方面是Docker与宿主机之间的安全问题

文章主要分析了Docker为了实现安全所采用的一些措施，比如使用Linux中的cgroups和namespace机制，以及使用Linux提供的AppArmor和SELinux安全模块。其实这些安全措施的基本思想，我认为都是资源隔离。通过资源隔离手段，让一个容器只能看到它所应该看到的资源。

最后，文章得出结论，Docker相比于虚拟机来说，能够实现更高密度的虚拟化环境，但是安全度比虚拟机要更低。但是，即使是使用默认配置，Docker本身也是**挺安全**的。给予一个容器太多特权，是比较危险的操作，更加安全的做法是不给容器特权（不知道理解得对不对🤣）。

## 3.文章各部分复述

### 摘要

### 1.介绍

说明了虚拟化技术的使用场景和意义。

然后告诉你虚拟化技术可以分为两类，一类是基于容器的虚拟化技术（比如Docker），一类是基于监管程序（虚拟机）。

### 2.虚拟化方法分析

介绍两种虚拟化技术。

基于容器：
- 操作系统层面
- 更加轻量级、节约资源
- 安全风险更高

基于监管程序
- 硬件层面
- 所需资源更多
- 安全性更高

### 3.Docker Overview

告诉你Docker的优点，轻量级、适用多平台、用户友好、对第三方工具支持较好等...

然后主要介绍了Docker中的镜像概念。

- 多层文件系统
- 修改镜像——写时复制

以及Docker使用namespace和cgroups，来为容器提供安全性。我觉得需要理解掌握的是namespace机制。

Linux中的namespace机制，类似于C++中的namespace思想。这一机制将所有资源根据不同的命名空间划分为不同的抽象整体。处于同一namespace中的进程可以看到对方，并且可以看到该命名空间下的资源及其变化情况。

文章中说目前（2015年）Docker使用5种namespace，但是现在已经是6种，分别为：

|  种类   |            含义            |
| :-----: | :------------------------: |
|   UTS   |         主机和域名         |
|   IPC   | 信号量、消息队列和共享内容 |
|   PID   |          进程编号          |
| network |  网络设备、网络栈、端口等  |
|  mount  |      挂载点(文件系统)      |
|  user   |        用户和用户组        |

### 4.Docker安全分析

这一部分内容，首先指出一个操作系统层面的虚拟化技术，如果要保持安全，那么应该满足6点：
- 进程隔离
- 文件系统隔离
- 设备隔离
- 进程间通信隔离
- 网络隔离
- 分配资源的限制

其实这些和之前提到的namespace的内容很相像，然后文章开始分析Docker如何满足这些需求。其实就是使用对应类型的namespace来实现不同类型资源的隔离。不过在说明网络资源隔离的时候，因为默认情况下，宿主机的虚拟网卡docker0会转发所有的数据包，所以可能存在ARP欺骗和泛洪攻击的风险，不过在后面的内容中，文章也说明可以通过在宿主机为虚拟网卡设置转发过滤规则来减少或避免这一风险。

接下来文章分析了Docker与宿主机之间的安全问题。

首先介绍了Linux中的capability概念。在以前的Linux版本中，内核将进程分为普通和root级别，root级别的进程拥有所有权限。显然这种方式是存在风险的。capability就是对于权限的更加细粒度的划分。Linux中有很多个capability，每个capability对应一个特殊的权限。

Docker默认关闭了很多capability，来确保容器与宿主机之间的安全。

接下来文章介绍了AppArmor和SELinux这两种Linux安全模块。

### 5.讨论与总结

## 4.个人总结

这篇文章是对Docker安全的总体分析，介绍了一些Docker安全相关的基础概念，比如namespace、capability。因为是总体性的概述类文章，所以内容并不多，一个下午的时间足够看完并且写出这样一篇总结。

## 参考资料
- [Linux namespace详解](https://www.cnblogs.com/sparkdev/p/9365405.html)
- [namespaces(7) — Linux manual page](https://man7.org/linux/man-pages/man7/namespaces.7.html)
- [使用clone函数](https://eli.thegreenplace.net/2018/launching-linux-threads-and-processes-with-clone/)
- [多种namespace示例](https://www.cnblogs.com/bakari/p/8560437.html)
