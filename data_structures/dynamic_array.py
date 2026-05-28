class DynamicArray:
    """A small dynamic array implementation with explicit capacity growth."""

    def __init__(self, initial_capacity=4):
        if initial_capacity <= 0:
            raise ValueError("initial_capacity must be positive")
        self._capacity = initial_capacity
        self._size = 0
        self._items = [None] * self._capacity

    def append(self, value):
        if self._size == self._capacity:
            self._resize(self._capacity * 2)
        self._items[self._size] = value
        self._size += 1

    def get(self, index):
        self._validate_index(index)
        return self._items[index]

    def set(self, index, value):
        self._validate_index(index)
        self._items[index] = value

    def remove(self, index):
        self._validate_index(index)
        value = self._items[index]
        for i in range(index, self._size - 1):
            self._items[i] = self._items[i + 1]
        self._size -= 1
        self._items[self._size] = None
        return value

    def pop(self):
        if self._size == 0:
            raise IndexError("pop from empty array")
        return self.remove(self._size - 1)

    def size(self):
        return self._size

    def capacity(self):
        return self._capacity

    def is_empty(self):
        return self._size == 0

    def to_list(self):
        result = []
        for i in range(self._size):
            result.append(self._items[i])
        return result

    def _resize(self, new_capacity):
        new_items = [None] * new_capacity
        for i in range(self._size):
            new_items[i] = self._items[i]
        self._items = new_items
        self._capacity = new_capacity

    def _validate_index(self, index):
        if index < 0 or index >= self._size:
            raise IndexError("index out of range")

    def __len__(self):
        return self._size

    def __iter__(self):
        for i in range(self._size):
            yield self._items[i]
