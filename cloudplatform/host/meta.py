class Meta:
    def __init__(self):
        self.storage = 0
        self.memory = 0
        self.address = '0.0.0.0'
        self.stats = False
        self.conn = None
        self.instances = []
        pass

    def __set__(self, instance, value):
        pass
