# sshsw

一个用于通过ssh访问交换机进行操作的工具。目前是针对DELL的交换机的，大家可以参照着代码修改成对应自己交换机的例子。

## 最简单的直接执行命令的例子

cmds中可以加入需要在交换机上执行的命令。

```python
    c = SWController(sw_host="172.18.9.2",
                     sw_port=22,
                     sw_user="testuser",
                     sw_passwd="testpassword")
    print c.exec_cmds(cmds=["enable", "testpassword", "exit"])
```
