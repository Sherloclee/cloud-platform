import json
import os
import socket
import struct
import threading
import time

import pymongo

from wsgiref.simple_server import make_server

import requests

from broadcast import BroadCast
from cloudplatform import utils
from cloudplatform.host.meta import Meta


class Host(threading.Thread):
    host = None  # type: str
    port = None  # type: int

    def __init__(self, broad_port, port, debug=False):
        super(Host, self).__init__()
        self.debug = debug
        self.domain = ""
        self.db = pymongo.MongoClient("mongodb://127.0.0.1:27017")["cloud_platform"]
        self.host = '127.0.0.1'  # local ip address
        self.broadcast = None
        self.broad_port = broad_port  # default 23335
        self.port = port
        self.childPid = -1
        self.meta_list = list()
        self.lock = threading.Lock()
        self.httpd_thread = None
        self.httpd = make_server(self.host, self.port, self.controller)
        self.flag = True

    def run(self):
        self.get_host()
        if self.debug:
            print "get host result:"
            print "hostname=%s" % self.host
        self.create_host_broadCast(self.broad_port)
        if self.debug:
            print "create_host_broadCast at %d" % self.broad_port

        self.httpd_thread = threading.Thread(target=self.httpd.serve_forever, name="httpd")
        self.httpd_thread.start()
        if self.debug:
            print "httpd start at %s:%d" % (self.host, self.port)

        loop = threading.Thread(target=self.__loop, name="loop")
        loop.start()
        if self.debug:
            print "server started..."
            print "api:%s:%d" % (self.host, self.port)

    def stop(self):
        self.flag = False
        self.destroy_host_broadCast()
        time.sleep(2)
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
        if self.debug:
            # print header
            # print request
            pass
        result = None
        if header == "instance":
            result = self.instanceController(request)
        if header == "web":
            result = self.webController(request)
        if header == "cli":
            result = self.command(request)

        response = {
            "request": request_body,
            "result": result
        }
        if self.debug:
            print result
            pass
        return [json.dumps(response)]

    def listener(self):
        pass

    def get_host(self):
        self.domain = socket.gethostname()
        self.host = socket.gethostbyname(self.domain)

    def create_host_broadCast(self, broad_port):
        ip = utils.htoi(self.host)
        package = struct.pack(">2I", self.port, ip)
        self.broadcast = BroadCast(broad_port, package)
        self.broadcast.start()

    def destroy_host_broadCast(self):
        self.broadcast.set_flag(False)

    def webController(self, request):
        method = request.get("method")
        sub_request = request.get("request")
        result = None
        if method == "account":  # account setting
            result = self.account(sub_request)

        if method == "instance":  # instance action
            result = self.instance(sub_request)

        response = {
            "controller": "success",
            "result": result
        }

        return response

    # webController
    def account(self, request):
        method = request.get("method")
        user_name = request.get("user_name")
        passwd = request.get("passwd")
        col = self.db["users"]
        response = None
        if method == "create":
            node = None
            for node in self.meta_list:
                if node.memory > (1024 * 1024):  # MiB
                    break

            node_name = node.hostname
            data = {
                "user_name": user_name,
                "passwd": passwd,
                "node": node_name
            }
            col.insert(data)

            meta_data = {
                "method": "CVN",
                "request": {
                    "user_name": user_name,
                    "passwd": passwd
                }
            }
            re = requests.post(node.url, json=meta_data)
            print node.url

            response = {
                "account": "success",
                "create": "success"
            }

        if method == "alter":
            myQuery = {"user_name": user_name}
            new_value = {"$set": {"user_name": user_name}}
            col.update(myQuery, new_value)
            response = {
                "account": "success",
                "alter": "success"
            }

        return response

    # webController
    def instance(self, request):
        print request
        user_name = request.get("user_name")
        col = self.db["users"]
        user = col.find_one({"user_name": user_name})
        print user_name
        print user
        node_name = user.get("node_name")  # find node_name by user_name

        node = None
        for node in self.meta_list:
            if node.hostname == node_name:  # find node
                break
        result = node.request(request)  # forward the request to node

        response = {
            "instance": "success",
            "result": result
        }

        return response

    def instanceController(self, request):
        method = request.get("method")
        sub_request = request.get("request")

        result = None
        if method == "regist":
            result = self.register(sub_request)
        if method == "heart":
            result = self.heart(sub_request)

        response = {
            "controller": "success",
            "result": result
        }
        return response

    def heart(self, request):
        node_name = request.get("node_name")
        for item in self.meta_list:
            if item.hostname == node_name:
                item.isAlive = True
        return {"heart": "success"}

    # noinspection PyBroadException
    def register(self, request):
        try:
            new_meta = Meta(request)
            self.meta_list.append(new_meta)
            for item in self.meta_list:
                print item.hostname, item.memory
            return {"stats": 200}
        except Exception:
            return {"stats": 500}

    def command(self, result):
        print result
        command = result.get("command")
        result = None
        print command
        if command == "stop":
            result = "server stop"
            temp = threading.Thread(target=self.stop)
            temp.start()

        response = {
            "command": "success",
            "result": result
        }
        return response


def local_test():
    host = Host(23333, 23334)
    host.get_host()
    # create test socket
    sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sk.bind(('', 23333))
    # create test broadcast
    host.create_host_broadCast(broad_port=23334)
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
    host = Host(23334, 23335)
    host.get_host()
    host.create_host_broadCast(broad_port=23334)
    raw_input()
    host.destroy_host_broadCast()


if __name__ == "__main__":
    remote_test()
