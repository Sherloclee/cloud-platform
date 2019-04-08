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

    try:
        conn = pymongo.MongoClient(mongo)
        db = conn["cloud_platforms"]
        db.create_collection("system_info")
        db.create_collection("route")
        col = db["system_info"]
        db_info = {
            "type": "gateway_info",
            "gateway_start": gateway_start,
            "current": 0,
        }
        col.insert(db_info)
    except Exception:
        print Exception.message
    conf_info = {
        "PLATFORM_ROOT": platform_root,
        "STORAGE_PATH": storage,
        "TEMPLATE_PATH": template
    }

    etc_file = open(etc, "w")
    etc_file.write(json.dumps(conf_info))
    etc_file.close()
