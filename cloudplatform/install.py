import json
import os
import shutil

import pymongo


def install():
    print os.getcwd()
    mongo = "mongodb://127.0.0.1:27017"
    gateway_start = 100
    etc = "/etc/platform.conf"
    platform_root = "/kvm/"
    storage = "/kvm/storage/"
    template = "/kvm/template/"

    storage_cloud_init = storage+"cloud_init/"
    storage_images = storage+"images/"
    storage_xml = storage+"xml/"
    storage_json = storage+"json/"

    if not os.path.exists(platform_root):
        os.mkdir(platform_root)
    if not os.path.exists(storage):
        os.mkdir(storage)
        os.mkdir(storage_cloud_init)
        os.mkdir(storage_images)
        os.mkdir(storage_xml)
        os.mkdir(storage_json)
    if not os.path.exists(template):
        # os.mkdir(template)
        shutil.copytree("./template", platform_root+"template/", True)

    conn = pymongo.MongoClient(mongo)
    db = conn["cloud_platform"]
    try:
        db.create_collection("system_info")
    except Exception:
        print Exception.message
    try:
        db.create_collection("route")
    except Exception:
        print Exception.message

    col = db["system_info"]
    gateway_info = {
        "type": "gateway_info",
        "gateway_start": gateway_start,
        "current": 0,
    }
    col.insert(gateway_info)
    ip_info = {
        "type": "ip_info",
        "ip_start": "10.66.106.21",
        "current": 0
    }
    col.insert(ip_info)

    conf_info = {
        "PLATFORM_ROOT": platform_root,
        "STORAGE_PATH": storage,
        "TEMPLATE_PATH": template
    }

    etc_file = open(etc, "w")
    etc_file.write(json.dumps(conf_info))
    etc_file.close()
