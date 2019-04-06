import json
import os
import socket
import struct
import threading
import time

import pymongo

from wsgiref.simple_server import make_server
from broadcast import BroadCast
from cloudplatform import utils
from cloudplatform.host.meta import Meta


class Host(threading.Thread):
    def __init__(self, broad_port, port):
        super(Host, self).__init__()
        self.domain = ""
        self.db = pymongo.MongoClient("mongodb://127.0.0.1:27017")["cloud_platform"]
        self.host = '127.0.0.1'
        self.broadcast = None
        self.broad_port = broad_port  # default 23335
        self.port = port
        self.childPid = -1
        self.meta_list = list()
        self.lock = threading.Lock()
        self.httpd_thread = None
        self.httpd = make_server(self.host, self.port, self.controller)
        os.dup2(open("/dev/null", "r").fileno(), self.httpd.fileno())
        self.flag = True

    def run(self):
        self.get_host()
        self.create_host_broadCast()

        self.httpd_thread = threading.Thread(target=self.httpd.serve_forever(), name="httpd")
        self.httpd_thread.start()

        loop = threading.Thread(target=self.__loop, name="loop")
        loop.start()

    def stop(self):
        self.flag = False
        self.destroy_host_broadCast()
        self.httpd.shutdown()

    def __resolve(self):
        pass

    @staticmethod
    def compare(elem):
        return elem.memory

    def __loop(self):
        while self.flag:
            self.lock.acquire()
            self.meta_list.sort(key=self.compare, reverse=False)
            self.lock.release()
            time.sleep(2)

    def controller(self, environ, start_response):
        start_response('200 OK', [('Content-Type', 'application/json')])
        request_body = environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0)))
        request_body = json.loads(request_body)

        header = request_body.get('header')
        request = request_body.get('request')

        response = None
        if header == "instance":
            response = self.instanceController(request)
        if header == "web":
            response = self.webController(request)
        return response

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

    def webController(self, request):
        request_type = request.get("type")
        sub_request = request.get("request")
        if request_type == "account":  # account setting
            return self.account(sub_request)

        if request_type == "instance":  # instance action
            return self.instance(sub_request)

    def account(self, request):
        method = request.get("method")
        user_name = request.get("user_name")
        passwd = request.get("passwd")
        col = self.db["users"]
        if method == "create":
            node = None
            for node in self.meta_list:
                if node.memory > (1024 * 1024):
                    break

            node_name = node.hostname
            data = {
                "user_name": user_name,
                "passwd": passwd,
                "node": node_name
            }
            col.insert(data)
            pass
        if method == "alter":
            myQuery = {"user_name": user_name}
            new_value = {"$set": {"user_name": user_name}}
            col.update(myQuery, new_value)
            pass
        pass

    def instance(self, request):
        user_name = request.get("user_name")
        col = self.db["users"]
        user = col.find_one({"user_name": user_name})
        node_name = user.get("node_name")  # find node_name by user_name
        node = None
        for node in self.meta_list:
            if node.hostname == node_name:  # find node
                break
        return node.request(request)  # forward the request to node

    pass

    def instanceController(self, request):
        method = request.get("method")
        sub_request = request.get("request")
        if method == "regist":
            return self.register(sub_request)

    def register(self, request):
        url = request.get("url")
        new_meta = Meta()
        new_meta.url = url
        self.meta_list.append(new_meta)
        return {"stats": 11}


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
