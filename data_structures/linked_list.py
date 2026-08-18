class LinkedListNode:
    """Node used by DoublyLinkedList."""

    def __init__(self, data):
        self.prev = None
        self.next = None
        self.data = data
        self._owner = None


class DoublyLinkedList:
    """Doubly linked list with O(1) node insertion, removal, and movement."""

    def __init__(self):
        self.head = None
        self.tail = None
        self._size = 0

    def insert_front(self, data):
        node = LinkedListNode(data)
        node._owner = self
        if self.head is None:
            self.head = node
            self.tail = node
        else:
            node.next = self.head
            self.head.prev = node
            self.head = node
        self._size += 1
        return node

    def insert_back(self, data):
        node = LinkedListNode(data)
        node._owner = self
        if self.tail is None:
            self.head = node
            self.tail = node
        else:
            node.prev = self.tail
            self.tail.next = node
            self.tail = node
        self._size += 1
        return node

    def remove_front(self):
        if self.head is None:
            return None
        return self.remove_node(self.head)

    def remove_back(self):
        if self.tail is None:
            return None
        return self.remove_node(self.tail)

    def remove_node(self, node):
        if node is None or node._owner is not self:
            return None

        if node.prev is None:
            self.head = node.next
        else:
            node.prev.next = node.next

        if node.next is None:
            self.tail = node.prev
        else:
            node.next.prev = node.prev

        node.prev = None
        node.next = None
        node._owner = None
        self._size -= 1
        return node.data

    def move_to_front(self, node):
        if node is None or node._owner is not self:
            return None
        if node is self.head:
            return node

        if node.prev is not None:
            node.prev.next = node.next
        if node.next is not None:
            node.next.prev = node.prev
        if node is self.tail:
            self.tail = node.prev

        node.prev = None
        node.next = self.head
        self.head.prev = node
        self.head = node
        return node

    def size(self):
        return self._size

    def is_empty(self):
        return self._size == 0

    def to_list(self):
        result = []
        current = self.head
        while current is not None:
            result.append(current.data)
            current = current.next
        return result

    def __len__(self):
        return self._size

    def __iter__(self):
        current = self.head
        while current is not None:
            yield current.data
            current = current.next
