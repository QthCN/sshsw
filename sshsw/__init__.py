# -*- coding: utf-8 -*-


import logging
import Queue
import socket
import time

import paramiko


class SWController(object):

    def __init__(self, sw_host, sw_port, sw_user, sw_passwd,
                 sw_admin_passwd=None, **kwargs):
        self.sw_host = sw_host
        self.sw_port = sw_port
        self.sw_user = sw_user
        self.sw_passwd = sw_passwd
        self.sw_admin_passwd = sw_admin_passwd

        self.queue = Queue.Queue()

        self.use_gss_api = kwargs.get("UseGSSAPI", True)
        self.use_do_gss_api_key_exchange = kwargs.get("DoGSSAPIKeyExchange",
                                                      True)

    def _get_client(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        logging.info("Connecting...")

        if (not self.use_gss_api or
                (not self.use_gss_api and
                     not self.use_do_gss_api_key_exchange)):
            client.connect(self.sw_host, self.sw_port,
                           self.sw_user, self.sw_passwd)
        else:
            hostname = socket.getfqdn(self.sw_host)
            try:
                client.connect(hostname, self.sw_port, self.sw_user,
                               gss_auth=self.use_gss_api,
                               gss_kex=self.use_do_gss_api_key_exchange)
            except Exception as e:
                logging.exception(e)
                logging.warn("Use username/password.")
                client.connect(self.sw_host, self.sw_port,
                               self.sw_user, self.sw_passwd)
        logging.info("Connect successful.")
        return client

    def _close_client(self, client):
        try:
            client.close()
        except Exception as e:
            logging.exception(e)

    def exec_commands(self, cmds=[], wait_output=True):
        cmds.append("exit")
        client = self._get_client()
        chan = client.invoke_shell()
        chan.settimeout(0.0)
        ssh_disconnected = False
        result = ""
        if wait_output:
            for cmd in cmds:
                output = ""
                while True:
                    try:
                        rx = chan.recv(1024)
                        if len(rx) == 0:
                            ssh_disconnected = True
                            break
                    except Exception as e:
                        break
                    output += rx

                if ssh_disconnected:
                    return result

                for c in cmd+"\n":
                    chan.send(c)

                result += output

            while True:
                try:
                    rx = chan.recv(1024)
                    if len(rx) == 0:
                        break
                except Exception as e:
                    continue
                result += rx
        else:
            for cmd in cmds:
                for c in cmd+"\n":
                    chan.send(c)
                time.sleep(0.5)
            time.sleep(1)

        chan.close()
        client.close()
        return result

    def get_enable_cmds(self):
        if self.sw_admin_passwd:
            return ["enable", self.sw_admin_passwd]
        else:
            return ["enable"]

    def show_run(self, blank_cnt=30):
        def _show_run(t):
            cmds = self.get_enable_cmds()
            cmds.append("show run")
            for c in range(0, t):
                cmds.append(" ")
            cmds.append("exit")

            output = self.exec_commands(cmds)
            return output

        result = _show_run(blank_cnt)

        output = ""
        in_cfg_section = False
        for l in result.split("\n"):
            if l.strip() == "!Current Configuration:":
                in_cfg_section = True
            if l.strip().endswith("#"):
                in_cfg_section = False
            if in_cfg_section:
                output += l.strip()
                output += "\n"

        return output

    def add_simple_acl(self, name, if_name, src_ip,
                       dst_ip, dst_mask, direction="in"):
        cmds = self.get_enable_cmds()
        cmds.append("conf t")
        cmds.append("ip access-list {0} extended".format(name))
        cmds.append("deny ip host {src_ip} {dst_ip} {dst_mask}".format(
            src_ip=src_ip,
            dst_ip=dst_ip,
            dst_mask=dst_mask
        ))
        cmds.append("permit ip any any")
        cmds.append("exit")
        cmds.append("interface {0}".format(if_name))
        cmds.append("ip access-group {name} {direction}".format(
            name=name,
            direction=direction
        ))
        cmds.append("exit")
        cmds.append("exit")
        cmds.append("exit")

        self.exec_commands(cmds, False)

if __name__ == "__main__":
    c = SWController(sw_host="10.2.3.4",
                     sw_port=22,
                     sw_user="user",
                     sw_passwd="tester",
                     sw_admin_passwd="testpasswd")
    sw_config = c.show_run()
    c.add_simple_acl("test_acl", "gigabitethernet 1/0/14",
                     "10.9.9.9", "192.0.0.0", "255.0.0.0",
                     "in")
