import unittest

from data_structures import BinarySearchTree, BinaryTree, BinaryTreeNode


class BinaryTreeTests(unittest.TestCase):
    def test_empty_tree_traversals(self):
        tree = BinaryTree()

        self.assertEqual(tree.preorder(), [])
        self.assertEqual(tree.inorder(), [])
        self.assertEqual(tree.postorder(), [])
        self.assertEqual(tree.level_order(), [])

    def test_preorder_inorder_postorder_and_level_order(self):
        tree = BinaryTree("A")
        left = tree.insert_left(tree.root, "B")
        right = tree.insert_right(tree.root, "C")
        tree.insert_left(left, "D")
        tree.insert_right(left, "E")
        tree.insert_right(right, "F")

        self.assertEqual(tree.preorder(), ["A", "B", "D", "E", "C", "F"])
        self.assertEqual(tree.inorder(), ["D", "B", "E", "A", "C", "F"])
        self.assertEqual(tree.postorder(), ["D", "E", "B", "F", "C", "A"])
        self.assertEqual(tree.level_order(), ["A", "B", "C", "D", "E", "F"])

    def test_rejects_foreign_parent_and_occupied_child(self):
        tree = BinaryTree("root")
        tree.insert_left(tree.root, "left")

        with self.assertRaises(ValueError):
            tree.insert_left(tree.root, "replacement")
        with self.assertRaises(ValueError):
            tree.insert_right(BinaryTreeNode("foreign"), "child")


class BinarySearchTreeTests(unittest.TestCase):
    def setUp(self):
        self.tree = BinarySearchTree()
        for value in [8, 3, 10, 1, 6, 14, 4, 7, 13]:
            self.tree.insert(value)

    def test_insert_search_and_sorted_inorder(self):
        self.assertEqual(self.tree.inorder(), [1, 3, 4, 6, 7, 8, 10, 13, 14])
        self.assertEqual(self.tree.search(6).data, 6)
        self.assertTrue(self.tree.contains(13))
        self.assertFalse(self.tree.contains(99))
        self.assertEqual(self.tree.size(), 9)

        original = self.tree.search(6)
        self.assertIs(self.tree.insert(6), original)
        self.assertEqual(self.tree.size(), 9)

    def test_delete_leaf_one_child_two_children_and_root(self):
        self.assertTrue(self.tree.delete(7))
        self.assertEqual(self.tree.inorder(), [1, 3, 4, 6, 8, 10, 13, 14])

        self.assertTrue(self.tree.delete(14))
        self.assertEqual(self.tree.inorder(), [1, 3, 4, 6, 8, 10, 13])

        self.assertTrue(self.tree.delete(3))
        self.assertEqual(self.tree.inorder(), [1, 4, 6, 8, 10, 13])

        self.assertTrue(self.tree.delete(8))
        self.assertEqual(self.tree.inorder(), [1, 4, 6, 10, 13])
        self.assertEqual(self.tree.root.data, 10)
        self.assertIsNone(self.tree.root.parent)
        self.assertEqual(self.tree.size(), 5)

        self.assertFalse(self.tree.delete(99))
        self.assertEqual(self.tree.size(), 5)


if __name__ == "__main__":
    unittest.main()
