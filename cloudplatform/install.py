import json
import os
import pymongo


def install():
    mongo = "mongodb://127.0.0.1:27017"
    gateway_start = 100
    etc = "/etc/platform.conf"
    platform_root = "/kvm/"
    storage = "/kvm/storage/"
    template = "/kvm/storage/"
    os.mkdir(platform_root)
    os.mkdir(storage)
    os.mkdir(template)

    conn = pymongo.MongoClient(mongo)
    db = conn["cloud_platform"]
    db.create_collection("system_info")
    db.create_collection("route")
    col = db["system_info"]
    db_info = {
        "gateway_start": gateway_start,
        "current": 0,
    }
    col.insert(db_info)

    conf_info = {
        "PLATFORM_ROOT": platform_root,
        "STORAGE_PATH": storage,
        "TEMPLATE_PATH": template
    }

    etc_file = open(etc, "w")
    etc_file.write(json.dump(etc_file, conf_info))
