class LinkedListNode:
    """DoublyLinkedList용 노드"""

    def __init__(self, data):
        """노드 데이터와 이전·다음 연결 및 소유 리스트 초기화"""

        self.prev = None
        self.next = None
        self.data = data
        self._owner = None


class DoublyLinkedList:
    """O(1) 노드 삽입, 삭제, 이동을 지원하는 DoublyLinkedList"""

    def __init__(self):
        """머리·꼬리 노드와 리스트 크기 초기화"""

        self.head = None
        self.tail = None
        self._size = 0

    def insert_front(self, data):
        """새 노드의 리스트 맨 앞 삽입 및 노드 반환"""

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
        """새 노드의 리스트 맨 뒤 삽입 및 노드 반환"""

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
        """리스트 맨 앞 노드 제거 및 데이터 반환"""

        return self.remove_node(self.head)

    def remove_back(self):
        """리스트 맨 뒤 노드 제거 및 데이터 반환"""

        return self.remove_node(self.tail)

    def remove_node(self, node):
        """현재 리스트가 소유한 특정 노드 제거 및 데이터 반환"""

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
        """현재 리스트가 소유한 특정 노드의 맨 앞 이동"""

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
        """현재 노드 개수 반환"""

        return self._size

    def is_empty(self):
        """리스트의 빈 상태 여부 확인"""

        return self._size == 0

    def to_list(self):
        """노드 데이터를 앞에서부터 담은 내장 리스트 반환"""

        return list(self)

    def __len__(self):
        """내장 len 호출을 위한 노드 개수 반환"""

        return self._size

    def __iter__(self):
        """머리부터 꼬리까지 노드 데이터 순회"""

        current = self.head
        while current is not None:
            yield current.data
            current = current.next
