class HashMapEntry:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None


class HashMap:
    """Hash map with separate chaining and explicit resize control."""

    def __init__(self, initial_capacity=8, max_load_factor=0.75):
        if initial_capacity <= 0:
            raise ValueError("initial_capacity must be positive")
        if max_load_factor <= 0:
            raise ValueError("max_load_factor must be positive")
        self._capacity = initial_capacity
        self._max_load_factor = max_load_factor
        self._size = 0
        self._buckets = [None] * self._capacity

    def put(self, key, value):
        bucket_index = self._bucket_index(key)
        current = self._buckets[bucket_index]
        while current is not None:
            if current.key == key:
                current.value = value
                return
            current = current.next

        entry = HashMapEntry(key, value)
        entry.next = self._buckets[bucket_index]
        self._buckets[bucket_index] = entry
        self._size += 1

        if self._load_factor() > self._max_load_factor:
            self._resize(self._capacity * 2)

    def get(self, key, default=None):
        entry = self._find_entry(key)
        if entry is None:
            return default
        return entry.value

    def remove(self, key):
        bucket_index = self._bucket_index(key)
        current = self._buckets[bucket_index]
        previous = None

        while current is not None:
            if current.key == key:
                if previous is None:
                    self._buckets[bucket_index] = current.next
                else:
                    previous.next = current.next
                current.next = None
                self._size -= 1
                return current.value
            previous = current
            current = current.next

        return None

    def contains(self, key):
        return self._find_entry(key) is not None

    def keys(self):
        result = []
        for i in range(self._capacity):
            current = self._buckets[i]
            while current is not None:
                result.append(current.key)
                current = current.next
        return result

    def size(self):
        return self._size

    def capacity(self):
        return self._capacity

    def _hash(self, key):
        text = str(key)
        hash_value = 0
        for char in text:
            hash_value = (hash_value * 31 + ord(char)) & 0x7FFFFFFF
        return hash_value

    def _bucket_index(self, key):
        return self._hash(key) % self._capacity

    def _find_entry(self, key):
        current = self._buckets[self._bucket_index(key)]
        while current is not None:
            if current.key == key:
                return current
            current = current.next
        return None

    def _load_factor(self):
        return self._size / self._capacity

    def _resize(self, new_capacity):
        old_buckets = self._buckets
        self._capacity = new_capacity
        self._buckets = [None] * self._capacity

        for i in range(len(old_buckets)):
            current = old_buckets[i]
            while current is not None:
                next_entry = current.next
                bucket_index = self._bucket_index(current.key)
                current.next = self._buckets[bucket_index]
                self._buckets[bucket_index] = current
                current = next_entry

    def __len__(self):
        return self._size
