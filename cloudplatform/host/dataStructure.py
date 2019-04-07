class Link_list:

    def __init__(self):
        self.head = None
        self.tail = None
        self.list = Link_node()
        self.len = 0
        self.head = self.list
        self.tail = self.list

    def append(self, meta):
        new_node = Link_node(meta)
        self.tail.next_node = new_node
        self.tail = self.tail.next_node

    def insert(self, meta, cmp):
        node = self.head
        while node.next_node is not None:
            if cmp(node):
                pass


class Link_node:
    def __init__(self, data=None):
        self.data = data
        self.next_node = None
