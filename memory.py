class MemoryManager:
    def __init__(self):
        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0

    def entry_size(self, key, value):
        return len(str(key).encode("utf-8")) + len(str(value).encode("utf-8"))

    def set_maxmemory(self, value):
        self.maxmemory = value

    def is_limited(self):
        return self.maxmemory > 0

    def can_store_entry(self, key, value):
        if not self.is_limited():
            return True
        return self.entry_size(key, value) <= self.maxmemory

    def add_entry(self, key, value):
        self.used_memory += self.entry_size(key, value)

    def replace_entry(self, key, old_value, new_value):
        self.used_memory += self.entry_size(key, new_value) - self.entry_size(key, old_value)

    def remove_entry(self, key, value):
        self.used_memory -= self.entry_size(key, value)
        if self.used_memory < 0:
            self.used_memory = 0

    def over_limit(self):
        return self.is_limited() and self.used_memory > self.maxmemory

    def record_eviction(self):
        self.evicted_keys += 1
