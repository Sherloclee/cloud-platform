# -*- coding: utf-8 -*-

import os
import syslog
from cloudplatform.meta.meta import Meta
import getopt

if __name__ == "__main__":
    try:
        pid = os.fork()
        if pid == 0:
            local = Meta()
            local.run()
            # cloudplatform.meta.meta.test("tony", "debug5a621", "192.168.127.1", 2, 20, 1, "CentOS", "VM5")
        else:
            print "start", pid
            syslog.syslog(syslog.LOG_INFO, "Cloud Platform starting with pid " + str(pid))
            exit(0)

    except OSError, e:

        syslog.syslog(syslog.LOG_ERR, OSError.message)
        exit(1)
