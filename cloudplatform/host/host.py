import socket
import struct
import threading

from wsgiref.simple_server import make_server
from broadcast import BroadCast
from cloudplatform import utils


class Host(threading.Thread):
    def __init__(self, broad_port, port):
        super(Host, self).__init__()
        self.domain = ""
        self.host = '127.0.0.1'
        self.broadcast = None
        self.broad_port = broad_port
        self.port = port
        self.childPid = -1
        self.meta_list = []

    def run(self):
        self.get_host()
        self.create_host_broadCast()

    def __resolve(self):
        pass

    def listener(self):
        pass

    def get_host(self):
        self.domain = socket.gethostname()
        self.host = socket.gethostbyname(self.domain)

    def create_host_broadCast(self):
        ip = utils.htoi(self.host)
        package = struct.pack(">2I", self.port, ip)
        self.broadcast = BroadCast(self.broad_port, package)
        self.broadcast.start()

    def destroy_host_broadCast(self):
        self.broadcast.set_flag(False)


def local_test():
    host = Host(23333, 23334)
    host.get_host()
    # create test socket
    sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sk.bind(('', 23333))
    # create test broadcast
    host.create_host_broadCast()
    # test recv data from broadcast
    recv_data, address = sk.recvfrom(1024)
    print address
    print struct.unpack(">2I", recv_data)
    recv_data, address = sk.recvfrom(1024)
    print address
    print utils.itoh(struct.unpack(">2I", recv_data)[1]), ":", struct.unpack(">2I", recv_data)[0]
    # test destroy broadcast
    host.destroy_host_broadCast()
    pass


def remote_test():
    host = Host(23333, 23334)
    host.get_host()
    host.create_host_broadCast()
    raw_input()
    host.destroy_host_broadCast()


if __name__ == "__main__":
    remote_test()
