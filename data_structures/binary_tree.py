from .linked_list import DoublyLinkedList


class BinaryTreeNode:
    """Node with explicit left and right child references."""

    def __init__(self, data):
        self.data = data
        self.left = None
        self.right = None
        self._owner = None


class BinaryTree:
    """General binary tree with the four standard traversal algorithms."""

    def __init__(self, root_data=None):
        self.root = None
        if root_data is not None:
            self.set_root(root_data)

    def set_root(self, data):
        """Create and return the root of an empty tree."""

        if self.root is not None:
            raise ValueError("root already exists")
        self.root = BinaryTreeNode(data)
        self.root._owner = self
        return self.root

    def insert_left(self, parent, data):
        """Insert and return a left child without replacing an existing child."""

        return self._insert_child(parent, data, "left")

    def insert_right(self, parent, data):
        """Insert and return a right child without replacing an existing child."""

        return self._insert_child(parent, data, "right")

    def preorder(self):
        """Return root-left-right traversal results."""

        result = []
        self._preorder(self.root, result)
        return result

    def inorder(self):
        """Return left-root-right traversal results."""

        result = []
        self._inorder(self.root, result)
        return result

    def postorder(self):
        """Return left-right-root traversal results."""

        result = []
        self._postorder(self.root, result)
        return result

    def level_order(self):
        """Return breadth-first results using a linked list as a queue."""

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
        if not isinstance(parent, BinaryTreeNode) or parent._owner is not self:
            raise ValueError("parent does not belong to this tree")
        if getattr(parent, side) is not None:
            raise ValueError(f"{side} child already exists")

        node = BinaryTreeNode(data)
        node._owner = self
        setattr(parent, side, node)
        return node

    def _preorder(self, node, result):
        if node is None:
            return
        result.append(node.data)
        self._preorder(node.left, result)
        self._preorder(node.right, result)

    def _inorder(self, node, result):
        if node is None:
            return
        self._inorder(node.left, result)
        result.append(node.data)
        self._inorder(node.right, result)

    def _postorder(self, node, result):
        if node is None:
            return
        self._postorder(node.left, result)
        self._postorder(node.right, result)
        result.append(node.data)
