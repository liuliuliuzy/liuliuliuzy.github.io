# Golang notes


## Go的package管理与GOPATH与go modules

- 关于`GOPATH`的作用
  - [http://c.biancheng.net/view/88.html](http://c.biancheng.net/view/88.html)

- 关于`go 1.11`之后引入的`go mudules`机制
  - [https://geektutu.com/post/quick-golang.html#9-%E5%8C%85-Package-%E5%92%8C%E6%A8%A1%E5%9D%97-Modules](https://geektutu.com/post/quick-golang.html#9-%E5%8C%85-Package-%E5%92%8C%E6%A8%A1%E5%9D%97-Modules)

上述两个链接中的内容讲得还不错。看一遍下来，感觉`GOPATH`就是过去的go用来管理组织项目的不同包的方式，而`go modules`是新的管理包的方式。在一个目录下执行`go mod init packagename`之后，就可以方便地引用该目录下的包。

## Go的interface学习

首先给出interface的定义语法：

```go
type inter1 interface {
    func1(x int)(int, error)
}
```

interface是一种抽象的类型，可以看作对一种规范的定义。接口定义的函数就是满足这种规范的具体类型所需要实现的方法。

接口一般被用在函数参数里，提供一种抽象的**函数对接**

比如，一个函数定义如下：

```
func userFunction(i inter1)(int error){
	...
}
```

那么对于实现了这个接口的类型，如：

```go
type s1 struct {
	...
}

func (s s1) func1(x int) (int, error) {
	...
}
```

我们就能够将`s1`类型的变量作为参数传入`userFunction()`中

需要注意的是，一种接口的**所有方法**被一种具体类型所实现，才能说这种类型实现了这个接口

#### 测试代码

```go
package main

import "fmt"

type pVal struct {
	val int
}

func (p pVal) fun() (int, error) {
	if p.val > 0 {
		return p.val, nil
	} else {
		return -1, fmt.Errorf("p.val 小于0: %d", p.val)
	}
}

//接口定义了一种规范、约定
type testInter interface {
	fun() (int, error)
	fun2() (int, error)
}

func userFunction(s testInter) int {
	res, err := s.fun()
	//error handle
	if err != nil {
		fmt.Println(err)
		return -1
	}
	return res
}

func main() {
	v1 := pVal{-1}
	fmt.Printf("type: %T\n", v1)
	res := userFunction(v1)
	fmt.Println(res)

	//接口的第二种用法
	var interVal testInter
	interVal = v1
	interVal.fun()

}

```
