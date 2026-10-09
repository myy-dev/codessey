import unittest

from data_structures import DoublyLinkedList, DynamicArray, HashMap, LinkedListNode, MinHeap


class DynamicArrayTests(unittest.TestCase):
    def test_append_get_set_remove_and_resize(self):
        array = DynamicArray(initial_capacity=2)

        array.append("a")
        array.append("b")
        array.append("c")

        self.assertEqual(array.size(), 3)
        self.assertEqual(array.capacity(), 4)
        self.assertEqual(array.get(0), "a")
        self.assertEqual(array.get(2), "c")

        array.set(1, "B")
        self.assertEqual(array.get(1), "B")
        self.assertEqual(array.remove(1), "B")
        self.assertEqual(array.to_list(), ["a", "c"])

    def test_invalid_index_raises(self):
        array = DynamicArray()
        with self.assertRaises(IndexError):
            array.get(0)


class DoublyLinkedListTests(unittest.TestCase):
    def test_insert_remove_and_move_to_front(self):
        linked_list = DoublyLinkedList()
        first = linked_list.insert_back("a")
        second = linked_list.insert_back("b")
        third = linked_list.insert_back("c")

        self.assertEqual(linked_list.to_list(), ["a", "b", "c"])
        linked_list.move_to_front(third)
        self.assertEqual(linked_list.to_list(), ["c", "a", "b"])
        self.assertIs(linked_list.head, third)
        self.assertIs(linked_list.tail, second)

        self.assertEqual(linked_list.remove_node(first), "a")
        self.assertEqual(linked_list.to_list(), ["c", "b"])
        self.assertEqual(linked_list.remove_front(), "c")
        self.assertEqual(linked_list.remove_back(), "b")
        self.assertTrue(linked_list.is_empty())

    def test_rejects_removed_or_foreign_nodes_without_corrupting_list(self):
        linked_list = DoublyLinkedList()
        first = linked_list.insert_back("a")
        linked_list.insert_back("b")

        self.assertEqual(linked_list.remove_node(first), "a")
        self.assertIsNone(linked_list.remove_node(first))
        self.assertIsNone(linked_list.remove_node(LinkedListNode("foreign")))
        self.assertEqual(linked_list.to_list(), ["b"])
        self.assertEqual(linked_list.size(), 1)


class HashMapTests(unittest.TestCase):
    def test_put_get_update_remove_and_resize(self):
        hash_map = HashMap(initial_capacity=2)

        hash_map.put("a", 1)
        hash_map.put("b", 2)
        hash_map.put("c", 3)

        self.assertGreaterEqual(hash_map.capacity(), 4)
        self.assertEqual(hash_map.get("a"), 1)
        self.assertEqual(hash_map.get("b"), 2)
        self.assertEqual(hash_map.get("c"), 3)

        hash_map.put("b", 20)
        self.assertEqual(hash_map.get("b"), 20)
        self.assertTrue(hash_map.contains("b"))
        self.assertEqual(hash_map.remove("b"), 20)
        self.assertFalse(hash_map.contains("b"))
        self.assertIsNone(hash_map.get("b"))
        self.assertEqual(hash_map.size(), 2)

    def test_collision_chain_with_small_capacity(self):
        hash_map = HashMap(initial_capacity=1)

        hash_map.put("a", "A")
        hash_map.put("b", "B")

        self.assertEqual(hash_map.get("a"), "A")
        self.assertEqual(hash_map.get("b"), "B")


class MinHeapTests(unittest.TestCase):
    def test_push_peek_pop_orders_values(self):
        heap = MinHeap()

        heap.push((30, "c"))
        heap.push((10, "a"))
        heap.push((20, "b"))
        heap.push((10, "aa"))

        self.assertEqual(heap.peek(), (10, "a"))
        self.assertEqual(heap.pop(), (10, "a"))
        self.assertEqual(heap.pop(), (10, "aa"))
        self.assertEqual(heap.pop(), (20, "b"))
        self.assertEqual(heap.pop(), (30, "c"))
        self.assertIsNone(heap.pop())
        self.assertTrue(heap.is_empty())


if __name__ == "__main__":
    unittest.main()
