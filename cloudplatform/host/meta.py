from requests import post


class Meta:
    def __init__(self, info_dict):
        self.hostname = info_dict.get("hostname")
        self.url = info_dict.get("url")
        self.storage = info_dict.get("storage")
        self.memory = info_dict.get("memory")
        self.address = info_dict.get("ip_address")
        self.vcpu = info_dict.get("v")
        self.stats = True
        self.isAlive = True

    def request(self, request):
        try:
            re = post(self.url, json=request)
            info = {
                "meta_request": "success",
                "result": re
            }
            return info
        except IOError:
            self.stats = False
            return {"meta_request": "failed"}

    def getMetaInfo(self):
        json_dict = {
            "method": "getInfo"
        }
        try:
            re = post(self.url, json=json_dict)
        except IOError:
            self.stats = False
            return {"meta_request": "failed"}
        response = re.json()
        self.storage = response.get("storage")
        self.memory = response.get("memory")
        self.vcpu = response.get("vcpu")
        self.stats = True
        return {"meta_info": "success"}

    def getInstanceInfo(self, request):
        re = post(self.url, request)
        return re.json()
        pass
