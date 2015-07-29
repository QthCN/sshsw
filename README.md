# sshsw

一个用于通过ssh访问交换机进行操作的工具。目前是针对DELL的交换机Dell Networking N2048P，大家可以参照着代码修改成对应自己交换机的例子。

## 最简单的直接执行命令的例子

cmds中可以加入需要在交换机上执行的命令。

```python
    c = SWController(sw_host="172.18.9.2",
                     sw_port=22,
                     sw_user="testuser",
                     sw_passwd="testpassword")
    sw_config = c.show_run()
    c.add_simple_acl("test_acl", "gigabitethernet 1/0/14",
                     "10.9.9.9", "192.0.0.0", "255.0.0.0",
                     "in")
```
