# Lc 204 经典题目-计算质数个数


经典数学题，计算小于n的质数的个数

<!-- more -->

> 统计所有小于非负整数 n 的质数的数量。
>
> 示例 1：
>
> > 输入：n = 10
> >
> > 输出：4
> >
> > 解释：小于 10 的质数一共有 4 个, 它们是 2, 3, 5, 7 。
>
> - 数据范围： `0 <= n <= 5 * 106`


一看今天的每日一题，难度简单，我心想这不是10分钟就把它给冲了？看完之后才发现，它说它是简单题，**它可不是简单题啊，它这是有备而来**，它明明就是一道数学题。

## 基础解法

最简单的想法当然是遍历从2开始的所有小于n的数，然后判断是否为质数，这样的话复杂度将会是$O(n \sqrt{n})$，意料之内，会超时，所以这种方法不行。

## 进阶

### 埃氏筛选
这种方法由希腊数学家厄拉多塞（Eratosthenes）提出，思路是遍历到一个质数$x$后，将其倍数$2\times x$、$3\times x$、$4\times x$...都标记为合数，这样利用了数与数之间的关联性，减少了很多没必要的判断质数操作。进一步优化其时间复杂度，可以发现，不用从$2\times x$开始，因为这样会对一个合数进行多次重复标记（比如$15 = 3\times 5$），在计算3时会乘以5，而计算5时又会乘以3。所以可以从$x\times x$开始标记。

```python
class Solution:
    def countPrimes(self, n: int) -> int:
        '''
        埃氏筛选法
        '''
        isPrime = [True for i in range(n)]
        res = 0
        for j in range(2, n):
            if isPrime[j]:
                res += 1
                print(j)
                tmp = j * j
                while tmp < n:
                    isPrime[tmp] = False
                    tmp += j
        
        return res
```

### 线性筛选
在埃氏筛选的基础上，还是会有重复的标记合数操作，比如30在遍历到3的时候，会被标记为合数($3\times 3 < 30$)，遍历到5的时候，又会被标记为合数。所以还需要对这个方法进行优化。前人已经想出的思路是空间换时间，在遍历的时候使用一个数组存储所遇见的质数，数组为\[$P_0, P_1, ..., P_i, ...$\]，并且对每个数$x$，将$x\times P_i$标记为合数，并且到$x\equiv 0 \pmod {P_i}$时结束。

因为假如$x \equiv 0 \pmod {P_i}$，然后再往后标记，即将$x \times P_{i+1}$标记为合数，那么因为$\frac{x}{P_i} \times P_{i+1} > x$，所以在后面遍历到$\frac{x}{P_i} \times P_{i+1}$这个数时，将其乘以$P_{i}$就会把$x \times P_{i+1}$标记为合数，与之前的操作重复，所以我们应该把到此停止，把$x \times P_{i+1}$这个数留给后面的大于$x$的数去标记。

```python
class Solution:
    def countPrimes(self, n: int) -> int:
        '''
        线性筛选法
        '''
        primes = []
        isPrime = [True for i in range(n)]
        for i in range(2, n):
            if isPrime[i]:
                primes.append(i)
            j = 0
            while j < len(primes) and i * primes[j] < n:
                isPrime[i * primes[j]] = False
                if i % primes[j] == 0:
                    break                
                j += 1
        # print(primes)
        return len(primes)
```

**时间复杂度： $O(n)$**，这一点是让我感觉比较出乎意料的，看来自己还是太菜了 :-(。
