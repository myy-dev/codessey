import time

from data_structures import HashMap, MinHeap


class TTLManager:
    """HashMap과 MinHeap 기반 최신 TTL 정보 관리"""

    def __init__(self, time_provider=None):
        self._expires = HashMap()
        self._heap = MinHeap()
        self._time_provider = time_provider or time.time

    def now(self):
        return self._time_provider()

    def set_expire(self, key, seconds):
        expire_at = self.now() + seconds
        self._expires.put(key, expire_at)
        self._heap.push((expire_at, key))

    def remove(self, key):
        self._expires.remove(key)

    def has_expire(self, key):
        return self._expires.contains(key)

    def is_expired(self, key):
        expire_at = self._expires.get(key)
        return expire_at is not None and expire_at <= self.now()

    def ttl(self, key):
        expire_at = self._expires.get(key)
        if expire_at is None:
            return -1

        remaining = int(expire_at - self.now())
        if remaining < 0:
            return 0
        return remaining

    def pop_expired_key(self):
        current_time = self.now()

        while not self._heap.is_empty():
            expire_at, key = self._heap.peek()
            if expire_at > current_time:
                return None

            self._heap.pop()
            latest_expire_at = self._expires.get(key)
            if latest_expire_at == expire_at:
                return key

        return None
