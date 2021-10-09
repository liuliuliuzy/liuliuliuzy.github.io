# Wsl迁移等操作记录


记录一下wsl迁移以及自选安装位置的一些操作。

打包

```
wsl --export distro_name file_name.tar
```

删除

```
wsl --unregister distro_name
```

导入（有看到[博客](https://www.cxyzjd.com/article/momodosky/108102146)说这里的`distro_name`需要与原本的`disrto_name`一致，不然会出问题，但我没试过。）

```
wsl --import distro_name install_location file_name.tar
```


设置用户为原先的默认用户

```
ubuntu2004 config --default-user <your_user_name>
```

wsl手动安装即可自己选择安装位置，在[官网](https://docs.microsoft.com/en-us/windows/wsl/install-manual)下载相应的发行版，然后将`.appx`后缀名改为`.zip`，解压到自定义的目录，点击exe安装即可。
