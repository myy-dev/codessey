from .dynamic_array import DynamicArray


class MinHeap:
    """DynamicArray 기반 MinHeap"""

    def __init__(self):
        self._items = DynamicArray()

    def push(self, value):
        self._items.append(value)
        self._heapify_up(self._items.size() - 1)

    def pop(self):
        if self.size() == 0:
            return None

        root = self._items.get(0)
        last = self._items.pop()
        if self.size() > 0:
            self._items.set(0, last)
            self._heapify_down(0)
        return root

    def peek(self):
        if self.size() == 0:
            return None
        return self._items.get(0)

    def size(self):
        return self._items.size()

    def is_empty(self):
        return self.size() == 0

    def to_list(self):
        return self._items.to_list()

    def _heapify_up(self, index):
        while index > 0:
            parent = (index - 1) // 2
            if self._items.get(parent) <= self._items.get(index):
                break
            self._swap(parent, index)
            index = parent

    def _heapify_down(self, index):
        size = self.size()
        while True:
            left = index * 2 + 1
            right = index * 2 + 2
            smallest = index

            if left < size and self._items.get(left) < self._items.get(smallest):
                smallest = left
            if right < size and self._items.get(right) < self._items.get(smallest):
                smallest = right

            if smallest == index:
                break
            self._swap(index, smallest)
            index = smallest

    def _swap(self, left, right):
        temp = self._items.get(left)
        self._items.set(left, self._items.get(right))
        self._items.set(right, temp)

    def __len__(self):
        return self.size()
