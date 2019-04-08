import socket
import threading
import syslog
from time import sleep


class BroadCast(threading.Thread):
    def __init__(self, port, message):
        super(BroadCast, self).__init__()
        self.message = message
        self.port = port
        self.conn = None
        self.flag = True

    def run(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        syslog.syslog(syslog.LOG_INFO, "Socket created")
        syslog.syslog(syslog.LOG_INFO, "Broadcast started at %d" % self.port)
        while self.flag:
            try:
                self.conn.sendto(self.message, ("<broadcast>", self.port))
            except IOError:
                print IOError.message
            sleep(2)
        self.conn.close()

    def set_flag(self, flag):
        self.flag = flag


if __name__ == "__main__":
    # sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # sk.bind(('', 23333))
    test = BroadCast(23333, "this is test data")
    test.start()
    # recv_data, address = sk.recvfrom(1024)
    # print("recv data:%s" % recv_data)
    # recv_data, address = sk.recvfrom(1024)
    # print("recv data:%s" % recv_data)
    # sk.close()
    ch = raw_input()
    test.set_flag(False)
