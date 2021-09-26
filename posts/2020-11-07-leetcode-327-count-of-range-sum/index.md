# Leetcode 327 count-of-range-sum


[Leetcode 327题](https://leetcode-cn.com/problems/count-of-range-sum/)

<!-- more -->

计算数组区间和的时候，经常用到前缀和这一思想。比如这题。

在看官方题解的第一种方法时，我无法理解为何可以在对前缀和数组进行归并排序的过程中，计算符合条件的区间数目。再看几遍才懂，当把左右两个已经排好序的数组进行归并的时候，因为左右的位置原因，所以可以保证右边数组中的元素减去左边数组中的元素所得到的结果，会是一个合法的区间和数据。再利用归并的递归思想，就可以得到想要的结果。

python代码如下：

```python
# 最容易理解的思路：前缀和
class Solution:
    def countRangeSum(self, nums: List[int], lower: int, upper: int) -> int:
        def countRec(lower: int, upper: int, left: int, right: int) -> int:
            if left == right:
                return 0
            # n1 n2 分别代表左半边和右半边前缀和数组中存在的符合条件的下标对数
            n1 = countRec(lower, upper, left, (left+right)//2)
            n2 = countRec(lower, upper, (left+right)//2+1, right)
            res = n1+n2

            # 接下来计算一个下标在左数组，一个下标在右数组的对数
            i = left
            L = R = (left+right)//2+1
            # 移动L与R
            while i <= (left+right)//2:
                while L<=right and sums[L]-sums[i] < lower:
                    L+=1
                while R<=right and sums[R]-sums[i] <= upper:
                    R+=1
                res += (R-L)
                i += 1
            # 为了保证左右数组的有序性，需要在这里进行归并排序
            # 创建临时数组
            sortedNums = []
            p1 = left
            p2 = (left+right)//2+1
            while p1 <= (left+right)//2 or p2 <= right:
                if p1 > (left+right)//2:
                    while p2 <= right:
                        sortedNums.append(sums[p2])
                        p2+=1
                elif p2 > right:
                    while p1 <= (left+right)//2:
                        sortedNums.append(sums[p1])
                        p1+=1
                else:
                    if sums[p1] < sums[p2]:
                        sortedNums.append(sums[p1])
                        p1+=1
                    else:
                        sortedNums.append(sums[p2])
                        p2+=1
            # 修改待排序数组
            for i in range(len(sortedNums)):
                sums[left+i] = sortedNums[i]

            return res
        # 首先计算前缀和数组
        sums = [0]
        for item in nums:
            sums.append(sums[-1]+item)

        return countRec(lower, upper, 0, len(nums))
```
