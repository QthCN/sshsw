# -*- coding: utf-8 -*-


import logging
import Queue
import select
import socket

import paramiko
from paramiko.py3compat import u


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

    def exec_cmds(self, cmds=[]):
        client = self._get_client()
        chan = client.invoke_shell()
        chan.settimeout(0.0)
        ssh_disconnected = False

        output = ""

        cmds.append("exit")

        for cmd in cmds:
            for c in cmd:
                self.queue.put(c)
            self.queue.put("\n")

        try:
            chan.settimeout(0.0)

            while True:
                while True:
                    try:
                        rx = u(chan.recv(1024))
                        if len(rx) == 0:
                            ssh_disconnected = True
                            break
                    except Exception as e:
                        break
                    output += rx

                if ssh_disconnected:
                    break

                try:
                    x = self.queue.get(timeout=0.1)
                    print x
                    chan.send(x)
                except Exception as e:
                    pass
        except Exception as e:
            logging.exception(e)
            output = "ERROR"

        chan.close()
        client.close()

        return output


if __name__ == "__main__":
    c = SWController(sw_host="127.0.0.1",
                     sw_port=22,
                     sw_user="root",
                     sw_passwd="rootroot")
    print c.exec_cmds(cmds=["cat /tmp/messages", "pwd", "ls"])
