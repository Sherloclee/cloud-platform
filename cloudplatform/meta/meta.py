import json
import socket
import platform
import os
import libvirt
import struct
import threading
import Queue
import pymongo
import jinja2
import requests

from wsgiref.simple_server import make_server
from cloudplatform import utils
from instance import Instance
from vnet import Vnet
from time import sleep

DATABASE_HOST = "127.0.0.1:27017"
ENV = os.environ['PLATFORM_ROOT']
TEMPLATE_PATH = ENV + "template/"
STORAGE_PATH = ENV + "storage/"


class Meta(threading.Thread):
    def __init__(self):
        # ipAddr of Host
        super(Meta, self).__init__()
        self.db = None
        self.conn = None
        self.host = '127.0.0.1'             # local ip address
        self.port = None                    # local port
        self.remote_host = None             # remote ip addr
        self.remote_port = None             # remote port
        self.kvm_version = None             # libvirt version
        self.OS = None                      # os
        self.memory = None                  # max ram size
        self.storage = None                 # max storage size
        self.api = None                     # api url
        self.queue = Queue.Queue()          # message queue
        self.httpd = make_server("0.0.0.0", 23334, self.__resolve)
        mongo_host = "mongodb://" + DATABASE_HOST
        mongo = pymongo.MongoClient(mongo_host)
        self.db = mongo['cloud_platform']   # mongodb

    def __connect(self, host, port):
        url = "http://%s:%d" % (host, port)
        data = {
            "method": "regist",
            "ip_address": self.host,
            "url": self.api,
            "maxVcpu": self.maxVcpu,
            "memory": self.memory,
        }
        re = requests.post(url, json=data)
        re = re.json()
        stats = re.get("stats")
        if stats == 200:
            return 1
        else:
            return 0

    def __resolve(self, environ, start_response):
        start_response('200 OK', [('Content-Type', 'application/json')])
        request_body = environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0)))
        request_body = json.loads(request_body)

        self.queue.put(request_body)
        response = {
            "result": "processing"
        }
        return [json.dumps(response)]

    def __get_system_info(self):
        session = libvirt.open("qemu:///system")
        self.mongo_host = "mongodb://127.0.0.1:27017"
        mongo = pymongo.MongoClient(self.mongo_host)
        self.db = mongo['cloud_platform']                       # mongodb conn
        self.hostname = socket.gethostname()                    # local host name
        self.host = socket.gethostbyname(self.hostname)       # local ip address
        self.kvm_version = session.getVersion()                 # libvirt version
        self.memory = session.getInfo()[1]                         # max memory size
        self.maxVcpu = session.getInfo()[3]                     # max Cpu core
        self.HDD = 256                                          # storage size
        self.port = 23333                                       # local api port
        self.OS = platform.system()                             # OS
        self.api = "http://%s:%d" % (self.host, self.port)    # local api port
        pass

    def run(self):
        self.__get_system_info()                                    # set server information
        remote_host, remote_port = self.__discoverHost()            # discover host server

        temp = threading.Thread(target=self.httpd.serve_forever)    # create api service
        temp.start()

        ctrl = threading.Thread(target=self.controller)             # create controller thread
        ctrl.start()

        for i in range(5):
            if self.__regist(remote_host, remote_port):            # regist meta to host
                break
        print "Meta server start..."
        print "Meta api %s:%d"

    def testVnet(self, flag, user_name, gateway):
        if flag:
            test_request = {
                "user_name": user_name,
                # "name": "sherlock-vnet",
                "gateway": gateway,
            }
            self.__createVnet(test_request)
        else:
            test_request = {
                "user_name": user_name,
                "name": gateway
            }
            self.__destroyVnet(test_request)

    def controller(self):
        message = json.load(self.queue.get())
        method = message.get('method')
        request = message.get('request')
        if method == 'CVM':  # create virtual machine
            self.__createVM(request)
            pass
        if method == 'CVN':  # create virtual net
            self.__createVnet(request)
            pass
        if method == 'DVM':  # destroy virtual machine
            self.__destroyVnet(request)
            pass
        if method == 'AVM':  # alter virtual machine
            self.__alterVM(request)
            pass
        if method == 'GVM':  # get virtual machine info
            self.__getVM(request)
        if method == 'getHost':

            pass

        pass

    def __discoverHost(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.conn.setblocking(False)
        self.conn.bind(('', 23333))
        for i in range(6):
            try:
                sleep(5)
                data, sock = self.conn.recvfrom(65535)
                port, ip_addr = struct.unpack(">2I", data)
                ip_addr = utils.itoh(ip_addr)
                return ip_addr, port
            except IOError:
                print("Discover host: Cannot find available host. Retrying...")
        print("Discover host: Cannot find any host.")
        pass

    def __createVM(self, request):
        user_name = request.get("user_name")
        instance_id = "%s-%s" % (user_name, request.get("instance_id"))
        memory = request.get("memory")
        disk_size = request.get("disk_size")
        linux = request.get("OSType")
        passwd = request.get("passwd")
        vcpu = request.get("vcpu")
        network = user_name

        # get vm sequence
        col = self.db[user_name]
        vnet = col.find({"name": user_name, "type": "vnet"})[0]
        gateway = vnet.get('gateway')
        gateway_int = utils.htoi(gateway)
        seq = vnet.get('seq')
        private_ip = utils.itoh(gateway_int + seq)
        nameserver = utils.itoh(gateway_int)
        net_segment = utils.itoh(gateway_int - 1)
        broadcast = utils.itoh(gateway_int + 254)

        cloud_init_dict = {
            "instance_id": instance_id,
            "passwd": passwd,
            "private_ip": private_ip,
            "net_segment": net_segment,
            "nameserver": nameserver,
            "broadcast": broadcast,
            "gateway": gateway
        }
        img = self.__createDisk(linux, instance_id, disk_size)
        cloud_init = self.__createCloudInit(cloud_init_dict)

        instance_dict = {
            "user_name": user_name,
            "instance_id": instance_id,
            "network": network,
            "vcpu": vcpu,
            "img": img,
            "memory": memory,
            "private_ip": private_ip,
            "cloud_init": cloud_init,
            "gateway": gateway
        }

        instance = Instance()
        instance.create(instance_dict)

        mongo_dict = {
            "name": instance_id,
            "instance_id": instance_id,
            "user_name": user_name,
            "network": network,
            "vcpu": vcpu,
            "memory": memory,
            "cloud_init": cloud_init,
            "gateway": gateway,
            "type": "VM",
            "private_ip": private_ip,
            "img": img,
            "os": linux
        }
        print user_name
        query = {"name": user_name, "type": "vnet"}
        new_value = {"$set": {"seq": seq + 1}}
        col.insert(mongo_dict)
        col.update(query, new_value)
        pass

    def __destroyVM(self, request):
        instance_id = request.get('instance_id')
        user_name = request.get('user_name')
        instance_id = "%s-%s" % (user_name, instance_id)
        col = self.db[user_name]
        json_dict = col.find({'instance_id': instance_id})[0]
        instance = Instance()
        instance.loadFromJson(json_dict)
        instance.destroy()
        col.remove({"instance_id": instance_id})
        pass

    def __alterVM(self, request):  # todo alter VM
        pass

    def __getVM(self, request):
        pass

    def __createVnet(self, request):  # todo create vnet
        """request:
            Example
            {
                "user_name":"sherlock",
                "name":"sherlock-vnet0",
                "gateway":"192.168.122.1",
                "netmask":"255.255.255.0",
                "mac":"52:54:00:0a:ba:59"
            }
        """
        user_name = request.get('user_name')
        json_dict = {'name': request.get('user_name'),
                     'type': 'vnet',
                     # 'netmask': '255.255.255.0',
                     'gateway': request.get('gateway'),
                     'seq': 1
                     # 'mac': request.get('mac')
                     }
        vnet = Vnet()
        vnet.create(json_dict)

        col = self.db[user_name]
        col.insert(json_dict)
        pass

    def __destroyVnet(self, request):
        """request:
        Example:
            {
                "user_name":"sherlock",
                "name":"sherlock"
            }
        """
        user_name = request.get('user_name')
        vnet_name = request.get("name")
        collection = self.db[user_name]
        json_dict = collection.find({"name": user_name})
        vnet = Vnet()
        vnet.loadFromJson(json_dict[0])
        vnet.destroy()
        collection.remove({"name": vnet_name})
        pass

    def testVM(self, flag, user_name, passwd, instance_id, vcpu, ram, disk_size, os_type):
        if flag:
            json_dict = {
                "user_name": user_name,
                "passwd": passwd,
                "instance_id": instance_id,
                "memory": ram,
                "disk_size": disk_size,
                "vcpu": vcpu,
                "OSType": os_type
            }
            self.__createVM(json_dict)
        else:
            json_dict = {
                "user_name": user_name,
                "instance_id": instance_id
            }
            self.__destroyVM(json_dict)
            pass
        pass

    @staticmethod
    def __createCloudInit(cloud_init_dict):
        instance_id = cloud_init_dict.get("instance_id")
        passwd = cloud_init_dict.get("passwd")
        private_ip = cloud_init_dict.get("private_ip")
        net_segment = cloud_init_dict.get("net_segment")
        nameserver = cloud_init_dict.get("nameserver")
        broadcast = cloud_init_dict.get("broadcast")
        gateway = cloud_init_dict.get("gateway")

        path = "%scloud_init/" % STORAGE_PATH
        file_name = "%s%s.img" % (path, instance_id)

        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_PATH + './cloud_init/'))
        user_source = jinja_env.get_template("user_data.yaml")
        user_data = user_source.render(
            passwd=passwd
        )
        user_data_file = "%s%s-user_data.yaml" % (path, instance_id)
        with open(user_data_file, "w") as fw:
            fw.write(user_data)

        meta_source = jinja_env.get_template("meta_data.yaml")
        meta_data = meta_source.render(
            instance_id=instance_id,
            passwd=passwd,
            private_ip=private_ip,
            netsegment=net_segment,
            nameserver=nameserver,
            broadcast=broadcast,
            gateway=gateway
        )
        meta_data_file = "%s%s-meta_data.yaml" % (path, instance_id)
        with open(meta_data_file, "w") as fw:
            fw.write(meta_data)

        command = "cloud-localds %s %s %s" % (file_name, user_data_file, meta_data_file)
        print command
        os.system(command)

        return file_name

    @staticmethod
    def __createDisk(linux, instance_id, disk_size):
        template_name = linux + '-template.qcow2 '

        file_name = instance_id + '.qcow2'
        img = STORAGE_PATH + './images/' + file_name
        base = TEMPLATE_PATH + './images/' + template_name
        command = "qemu-img create -b " + base + "-f qcow2 " + img + " " + str(disk_size) + "G"
        print command
        os.system(command)
        return img

    def __regist(self, remote_host, remote_port):
        url = "http://%s:%d" % (remote_host, remote_port)
        data = {
            "method": "regist",
            "ip_address": self.host,
            "url": self.api,
            "maxVcpu": self.maxVcpu,
            "memory": self.memory,
            "storage": self.storage,
        }
        re = requests.post(url, json=data)
        re = re.json()
        stats = re.get("stats")
        if stats == 200:
            return 1
        else:
            return 0
        pass


class Connector(threading.Thread):
    def __init__(self, host, port, callback):
        super(Connector, self).__init__()
        self.host = host
        self.port = port
        self.callback = callback
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.flag = True

    def run(self):
        self.sock.bind((self.host, self.port))
        while self.flag:
            try:
                data, conn = self.sock.recv(1024)
                self.callback(data)
            except IOError:
                pass

    def stop(self):
        self.flag = False
        self.sock.close()
        pass


def test(user_name, passwd, gateway, ram, disk_size, vcpu, OSType, instance_id):
    test_meta = Meta()
    print "Vnet:%s creating..." % user_name
    test_meta.testVnet(True, user_name, gateway)
    print "Vnet:%s create done!" % user_name
    # raw_input()

    print "VM:%s-%s creating..." % (user_name, instance_id)
    test_meta.testVM(True, user_name, passwd, instance_id, vcpu, ram, disk_size, OSType)
    print "VM:%s-%s create done" % (user_name, instance_id)
    # raw_input()
    print "VM:%s-%s destroying..." % (user_name, instance_id)
    test_meta.testVM(False, user_name, passwd, instance_id, vcpu, ram, disk_size, OSType)
    print "VM:%s-%s destroy done!" % (user_name, instance_id)
    print "VM test done!"

    print "Vnet:%s destroying..." % user_name
    test_meta.testVnet(False, user_name, gateway)
    print "Vnet:%s destroy done!" % user_name
    print "vnet test done!"
    # notice Vnet Done!


if __name__ == "__main__":
    test("sherlock", "debug5a621", "192.168.123.1", 2, 20, 1, "CentOS", "VM2")
    pass
