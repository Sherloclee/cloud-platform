from requests import post


class Meta:
    def __init__(self, info_dict):
        self.hostname = info_dict.get("hostname")
        self.url = info_dict.get("url")
        self.storage = info_dict.get("storage")
        self.memory = info_dict.get("memory")
        self.address = info_dict.get("ip_address")
        self.stats = True
        self.isAlive = True
        self.instances = info_dict.get("instance_list")

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
            "method": "getHost"
        }
        try:
            re = post(self.url, json=json_dict)
        except IOError:
            self.stats = False
            return {"meta_"}
        response = re.json()
        self.storage = response.get("storage")
        self.memory = response.get("memory")
        self.instances = response.get("instances")
        self.stats = True
        return {"meta_info": "success"}

    def getInstanceInfo(self, request):
        re = post(self.url, request)
        return re.json()
        pass
