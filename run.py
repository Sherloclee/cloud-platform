# -*- coding: utf-8 -*-

import os
import sys
import syslog
import getopt

from cloudplatform.install import install

debug = True
release = False


def test_meta():
    from cloudplatform.meta.meta import Meta

    try:
        pid = os.fork()
        if pid:
            print "start", pid
            syslog.syslog(syslog.LOG_INFO, "Cloud Platform starting with pid " + str(pid))
            exit(0)
        else:
            with open('/dev/null', "r") as read_null, open('/dev/null', 'w') as write_null:
                os.dup2(read_null.fileno(), sys.stdin.fileno())
                os.dup2(write_null.fileno(), sys.stdout.fileno())
                os.dup2(write_null.fileno(), sys.stderr.fileno())
            local = Meta()
            local.run()

    except OSError:
        syslog.syslog(syslog.LOG_ERR, OSError.message)
        exit(1)


def test_host():
    from cloudplatform.host.host import Host
    try:
        pid = os.fork()
        if pid:
            exit(0)
        else:
            test = Host(port=23335, broad_port=23334)
            test.run()

    except OSError:
        exit(1)


def test1():
    from cloudplatform.host import Host
    host = Host(port=23335, broad_port=23334, debug=debug)
    host.start()
    raw_input()
    host.stop()


def test2():
    from cloudplatform.meta.meta import Meta
    meta = Meta()
    meta.run()
    raw_input()
    meta.stop()


if __name__ == "__main__":
    arg = sys.argv[1]
    if arg == "host":
        test1()
    if arg == "meta":
        test2()
    if arg == "install":
        install()
