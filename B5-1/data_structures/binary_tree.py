from .linked_list import DoublyLinkedList


class BinaryTreeNode:
    """명시적 left·right 자식 참조를 포함하는 BinaryTreeNode"""

    def __init__(self, data):
        """노드 데이터, 좌우 자식, 소유 트리 초기화"""

        self.data = data
        self.left = None
        self.right = None
        self._owner = None


class BinaryTree:
    """네 가지 표준 순회를 지원하는 BinaryTree"""

    def __init__(self, root_data=None):
        """빈 트리 또는 초기 루트 데이터를 포함한 트리 초기화"""

        self.root = None
        if root_data is not None:
            self.set_root(root_data)

    def set_root(self, data):
        """빈 BinaryTree의 root 생성 및 반환"""

        if self.root is not None:
            raise ValueError("root 중복 생성")
        self.root = BinaryTreeNode(data)
        self.root._owner = self
        return self.root

    def insert_left(self, parent, data):
        """기존 자식 대체 없는 left 자식 삽입 및 반환"""

        return self._insert_child(parent, data, "left")

    def insert_right(self, parent, data):
        """기존 자식 대체 없는 right 자식 삽입 및 반환"""

        return self._insert_child(parent, data, "right")

    def preorder(self):
        """전위 순회(현재 노드·왼쪽·오른쪽 순서) 결과 반환"""

        result = []
        self._preorder(self.root, result)
        return result

    def inorder(self):
        """중위 순회(왼쪽·현재 노드·오른쪽 순서) 결과 반환"""

        result = []
        self._inorder(self.root, result)
        return result

    def postorder(self):
        """후위 순회(왼쪽·오른쪽·현재 노드 순서) 결과 반환"""

        result = []
        self._postorder(self.root, result)
        return result

    def level_order(self):
        """DoublyLinkedList queue 기반 level-order 순회 결과"""

        if self.root is None:
            return []

        result = []
        queue = DoublyLinkedList()
        queue.insert_back(self.root)
        while not queue.is_empty():
            node = queue.remove_front()
            result.append(node.data)
            if node.left is not None:
                queue.insert_back(node.left)
            if node.right is not None:
                queue.insert_back(node.right)
        return result

    def _insert_child(self, parent, data, side):
        """부모 소속과 자식 위치 검증 후 지정 방향의 자식 삽입"""

        if not isinstance(parent, BinaryTreeNode) or parent._owner is not self:
            raise ValueError("parent의 트리 소속 불일치")
        if getattr(parent, side) is not None:
            raise ValueError(f"{side} child 중복 생성")

        node = BinaryTreeNode(data)
        node._owner = self
        setattr(parent, side, node)
        return node

    def _preorder(self, node, result):
        """전위 순회(현재 노드·왼쪽·오른쪽 순서) 결과 누적"""

        if node is None:
            return
        result.append(node.data)
        self._preorder(node.left, result)
        self._preorder(node.right, result)

    def _inorder(self, node, result):
        """중위 순회(왼쪽·현재 노드·오른쪽 순서) 결과 누적"""

        if node is None:
            return
        self._inorder(node.left, result)
        result.append(node.data)
        self._inorder(node.right, result)

    def _postorder(self, node, result):
        """후위 순회(왼쪽·오른쪽·현재 노드 순서) 결과 누적"""

        if node is None:
            return
        self._postorder(node.left, result)
        self._postorder(node.right, result)
        result.append(node.data)
