# Leetcode 493 翻转对


- [Leetcode 493题](https://leetcode-cn.com/problems/reverse-pairs/)
- 难度：困难

<!-- more -->

想把这题记录下来的原因，主要是题解的归并算法思路比较典型，所以希望能够记住并掌握这种方法。

题目要求对一个数组进行处理，计算出所有满足`nums[i] > 2*nums[j]`且`i < j`的`(i, j)`对的个数。测试用例中最长数组长度为50000。那很显然，不能两次遍历，因为O(n^2)肯定会超时的。所以需要寻求其他方法。

再次思考要求，`i`与`j`的前后顺序是确定的，而且又是处理数组，并且要求低于O(n^2)的复杂度，所以应该想到归并排序（当然现在的我是上帝视角🤣）。

归并排序的过程中，每次合并两个已经排好序的数组时，对于固定前后顺序的下标处理就会变得简单许多了。

在实现的时候，还可以继续对处理过程进行部分优化，python3实现代码如下：

```python
from typing import List
import time
import random

class Solution:
    def reversePairs(self, nums: List[int]) -> int:
        '''
        这样就不超时了
        但是还是很慢🙄
        '''
        def countPairs(left: int, mid: int, right: int) -> int:
            res = 0
            lastj = mid + 1
            # 由于左右两边是已经排好序的，所以这里可以优化，对第一个之后的i，j并不需要从头开始遍历
            for i in range(left, mid + 1):
                while lastj <= right and nums[i] > 2 * nums[lastj]:
                    lastj += 1
                res += lastj - (mid + 1)
            return res
        
        def mergeAndCount(left: int, right: int) -> int:
            if left == right: return 0
            mid = (left + right) // 2
            res = mergeAndCount(left, mid) + mergeAndCount(mid + 1, right) + countPairs(left, mid, right)
            i,j,k = left, mid+1, left
            while i < mid+1 and j < right+1:
                if nums[i] < nums[j]: 
                    sortedNums[k] = nums[i]
                    i += 1
                else:
                    sortedNums[k] = nums[j]
                    j += 1
                k += 1
            
            while i < mid+1:
                sortedNums[k] = nums[i]
                i += 1
                k += 1

            while j < right+1:
                sortedNums[k] = nums[j]
                j += 1
                k += 1
            
            for t in range(left, right+1):
                nums[t] = sortedNums[t]
            
            return res

        if not nums:
            return 0
        sortedNums = [0 for i in range(len(nums))]
        return mergeAndCount(0, len(nums)-1)
                
if __name__ == "__main__":
    s = Solution()
    nums = [1, 26, 20, 66, 28, 75, 78, 15, 40, 64]
    # random.seed(time.time())
    # for i in range(10):
    #     nums.append(random.randrange(1,100))
    print(nums)
    print(s.reversePairs(nums))
    print(nums)
            
```

[327](https://leetcode-cn.com/problems/count-of-range-sum/)题同样也用到了这个思想，博客记录[在这](https://liuliuliuzy.github.io/2020/11/07/Leetcode-327-count-of-range-sum/)

