class BinarySearchTreeNode:
    """parent 참조를 포함하는 BinarySearchTree 노드"""

    def __init__(self, data):
        self.data = data
        self.left = None
        self.right = None
        self.parent = None


class BinarySearchTree:
    """삽입, 검색, 삭제, 정렬 순회를 지원하는 BinarySearchTree"""

    def __init__(self):
        self.root = None
        self._size = 0

    def insert(self, data):
        """데이터 삽입 및 노드 반환, 중복 값의 기존 노드 재사용"""

        if self.root is None:
            self.root = BinarySearchTreeNode(data)
            self._size = 1
            return self.root

        parent = None
        current = self.root
        while current is not None:
            parent = current
            # 중복값은 새 노드로 삽입하지 않고 기존 노드 반환
            if data == current.data:
                return current
            if data < current.data:
                current = current.left
            else:
                current = current.right

        node = BinarySearchTreeNode(data)
        node.parent = parent
        if data < parent.data:
            parent.left = node
        else:
            parent.right = node
        self._size += 1
        return node

    def search(self, data):
        """데이터 포함 노드 반환, 부재 시 None"""

        current = self.root
        while current is not None:
            if data == current.data:
                return current
            if data < current.data:
                current = current.left
            else:
                current = current.right
        return None

    def contains(self, data):
        return self.search(data) is not None

    def delete(self, data):
        """존재 데이터 삭제 및 트리 변경 여부 반환"""

        node = self.search(data)
        if node is None:
            return False

        if node.left is None:
            self._transplant(node, node.right)
        elif node.right is None:
            self._transplant(node, node.left)
        else:
            successor = self._minimum(node.right)
            if successor.parent is not node:
                self._transplant(successor, successor.right)
                successor.right = node.right
                successor.right.parent = successor
            self._transplant(node, successor)
            successor.left = node.left
            successor.left.parent = successor

        node.left = None
        node.right = None
        node.parent = None
        self._size -= 1
        return True

    def inorder(self):
        """오름차순 전체 값 반환"""

        result = []
        self._inorder(self.root, result)
        return result

    def size(self):
        return self._size

    def is_empty(self):
        return self._size == 0

    def _minimum(self, node):
        current = node
        while current.left is not None:
            current = current.left
        return current

    def _transplant(self, old_node, new_node):
        if old_node.parent is None:
            self.root = new_node
        elif old_node is old_node.parent.left:
            old_node.parent.left = new_node
        else:
            old_node.parent.right = new_node

        if new_node is not None:
            new_node.parent = old_node.parent

    def _inorder(self, node, result):
        if node is None:
            return
        self._inorder(node.left, result)
        result.append(node.data)
        self._inorder(node.right, result)
