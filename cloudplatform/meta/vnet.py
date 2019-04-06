import libvirt
import jinja2
import os

ENV = os.environ.get("PLATFORM_ROOT")
TEMPLATE_PATH = str(ENV) + "template/"
STORAGE_PATH = str(ENV) + "storage/"


class Vnet:
    def __init__(self):
        self.name = None
        self.gateway = None
        self.netmask = None
        # self.mac = None
        pass

    def create(self, json_dict):
        self.loadFromJson(json_dict)
        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_PATH + './xml/'))
        template = jinja_env.get_template("vnet_template.xml")
        content = template.render(
            name=self.name,
            gateway=self.gateway,
            netmask=self.netmask,
            # mac=self.mac
        )
        session = libvirt.open('qemu:///system')
        vnet = session.networkDefineXML(content)
        vnet.create()
        vnet.setAutostart(True)
        pass

    def loadFromJson(self, json_dict):
        self.name = json_dict.get('name')
        self.gateway = json_dict.get('gateway')
        self.netmask = '255.255.255.0'
        # self.mac = json_dict.get('mac')

    def destroy(self):
        if self.name is None:
            raise Exception("Vnet must be load or create")
        session = libvirt.open("qemu:///system")
        vnet = session.networkLookupByName(self.name)
        vnet.destroy()
        vnet.undefine()
