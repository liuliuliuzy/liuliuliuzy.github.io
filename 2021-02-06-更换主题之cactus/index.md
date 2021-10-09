# 更换主题之cactus


### 更换主题的原因

本博客以前的主题是[fluid](https://github.com/fluid-dev/hexo-theme-fluid)，刚开始觉得看着非常舒服，也比较简洁。但是用久了就发现，每次当我想创建一篇博客记录一下自己的想法时，我都要去找首页的缩略图素材和博客的背景图素材。对于本来就比较懒散的我来说，这无疑是比较折磨的。于是，我想着开设博客的初心是写作，主体还应该是文字。所以，在看过几个使用[cactus](https://probberechts.github.io/hexo-theme-cactus/)主题的大佬博客之后，我决定把主题也改为cactus。究其原因，我想是为了减少场外因素，提高自己的专注度吧。

### 数学公式渲染

在更换主题为cactus之后，我发现原本的数学公式渲染不出来了。嗯，遇到问题就去谷歌吧。在尝试了几次之后，我按照[这篇博客](https://qingstudios.com/2020/03/01/Hexo%E4%B8%AD%E6%8F%92%E5%85%A5%E6%95%B0%E5%AD%A6%E5%85%AC%E5%BC%8F/)的方法解决了数学公式渲染的问题。

总的来说，需要卸载hexo原本的`hexo-renderer-marked`，然后安装`hexo-renderer-kramed`和`hexo-renderer-mathjax`。如果之前像我一样安装过`hexo-math`的话，也需要把`hexo-math`卸载。

最后再修改一些历史遗留问题就能够在网页上看到数学公式了。

### 一些注意点

- 写作的时候一定要遵循markdown的语法规范。多行代码块的前后一定要留空行，否则当后面的内容中有行内代码块时，在渲染的时候`<code>`块就不会继承段落P的样式属性，造成行内代码块独占一行的情况。

- 修改`themes\cactus\source\css\style.styl`文件中的`code`处，增加自定义的`background-color`属性，可以自定义行内代码块的背景颜色，原主题的同色有点不太好看。
