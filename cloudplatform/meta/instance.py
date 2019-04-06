import libvirt
import os
import jinja2

ENV = os.environ.get("PLATFORM_ROOT")
TEMPLATE_PATH = str(ENV) + "template/"
STORAGE_PATH = str(ENV) + "storage/"

''' instance json data
{
    instance_id: name of instance 
    os: the OS of instance
    disk: virtual disk size
    img: virtual disk (type: qcow2)
    network: virtual internet interface
    public_ip
    private_IP
}
'''


class Instance:
    def __init__(self):
        self.kvm = libvirt.open('qemu:///system')
        self.instance_id = None
        self.os = "Linux"
        self.vcpu = 0
        self.ram = 0  # KiByte
        self.disk = 20  # GiByte
        self.network = 'virbr0'
        self.status = 'shutdown'
        self.xml_file = 'default.xml'
        self.private_ip = '0.0.0.0'
        self.public_ip = '0.0.0.0'
        self.gateway = None
        self.img = 'default.qcow2'
        self.cloud_init = None
        self.uuid = None
        pass

    def loadFromJson(self, json_dict):
        self.private_ip = json_dict.get('private_ip')
        self.public_ip = json_dict.get('public_ip')
        self.vcpu = json_dict.get('vcpu')
        self.ram = json_dict.get('memory')
        self.instance_id = json_dict.get('instance_id')
        self.os = json_dict.get('os')
        self.disk = json_dict.get('disk_size')
        self.img = json_dict.get('img')
        self.network = json_dict.get('network')
        self.cloud_init = json_dict.get('cloud_init')

    def destroy(self):
        session = libvirt.open('qemu:///system')
        instance = session.lookupByName(self.instance_id)
        instance.destroy()
        instance.undefine()

    def create(self, json_dict):
        """
        :param json_dict: json_dict
        :return: none
        """
        session = libvirt.open('qemu:///system')

        self.vcpu = json_dict.get('vcpu')
        self.ram = json_dict.get('memory')
        self.instance_id = json_dict.get('instance_id')
        self.os = json_dict.get('os')
        self.disk = json_dict.get('disk_size')
        self.img = json_dict.get('img')
        self.network = json_dict.get('network')
        self.cloud_init = json_dict.get('cloud_init')
        self.private_ip = json_dict.get('private_ip')
        self.gateway = json_dict.get('gateway')
        # create xml file from template
        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_PATH + './xml/'))
        template = jinja_env.get_template("instance_template.xml")
        content = template.render(
            instance_id=self.instance_id,
            memory=self.ram,
            vcpu=self.vcpu,
            network=self.network,
            img=self.img,
            cloud_init=self.cloud_init,
            private_ip=self.private_ip,
            gateway=self.gateway
        )

        self.uuid = self.instance_id
        xml_file_name = self.uuid + ".xml"
        path = STORAGE_PATH + "xml/" + xml_file_name
        with open(path, 'w') as xml_file:
            xml_file.write(content)
        # print content
        instance = session.defineXML(content)
        instance.create()

    def reboot(self):
        session = libvirt.open('qemu:///system')
        instance = session.lookupByName(self.instance_id)
        instance.reboot()
        pass

    def resize_ram(self, new_size):
        """
        :param new_size: new memory size KiB
        """
        session = libvirt.open('qemu:///system')
        instance = session.lookupByName(self.instance_id)
        instance.setMemory(new_size)

    def getVM(self):
        session = libvirt.open('qemu:///system')
        instance = session.lookupByName(self.instance_id)
        return instance


if __name__ == "__main__":
    pass
