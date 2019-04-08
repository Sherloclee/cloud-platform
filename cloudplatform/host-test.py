import json

import jinja2
import os

import requests

ENV = os.environ['PLATFORM_ROOT']
TEMPLATE_PATH = ENV + "template/"


def test_createUser():
    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_PATH + './json/'))
    template = jinja_env.get_template("create_user-template.json")
    content = template.render(
        user_name="sherlock",
        passwd="debug5a621"
    )
    data = json.loads(content)
    print data
    re = requests.post("http://127.0.0.1:23335", json=data)
    print re.json()


def test_createVM():
    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_PATH + './json/'))
    template = jinja_env.get_template("create_vm-template.json")
    content = template.render(
        user_name="sherlock",
        instance_id="VM1",
        passwd="debug5a621",
        OSType="CentOS",
        vcpu=1,
        memory=1024,
        disk_size=20
    )
    print content
    data = json.loads(content)
    re = requests.post("http://127.0.0.1:23335", json=data)


def test_destroyVM():
    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_PATH + './json/'))
    template = jinja_env.get_template("destroy_vm-template.json")
    content = template.render(
        user_name="sherlock",
        instance_id="VM1"
    )
    print content
    data = json.loads(content)
    re = requests.post("http://127.0.0.1:23335", json=data)


if __name__ == '__main__':
    # test_destroyVM()
    # test_createVM()
    # test_createUser()
    pass
