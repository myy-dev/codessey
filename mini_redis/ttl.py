import time

from data_structures import HashMap, MinHeap


class TTLManager:
    """HashMap과 MinHeap 기반 최신 TTL 정보 관리"""

    def __init__(self, time_provider=None):
        """최신 만료 시각 맵과 만료 순서 힙 초기화"""

        self._expires = HashMap()
        self._heap = MinHeap()
        self._time_provider = time_provider or time.time

    def now(self):
        """주입된 시간 제공자의 현재 시각 반환"""

        return self._time_provider()

    def set_expire(self, key, seconds):
        """키의 최신 만료 시각 저장 및 만료 순서 힙 추가"""

        expire_at = self.now() + seconds
        self._expires.put(key, expire_at)
        self._heap.push((expire_at, key))

    def remove(self, key):
        """최신 TTL 맵에서 키 제거 및 기존 힙 기록 유지"""

        self._expires.remove(key)

    def has_expire(self, key):
        """키의 만료 시간 설정 여부 확인"""

        return self._expires.contains(key)

    def is_expired(self, key):
        """키의 만료 시각 도달 여부 확인"""

        expire_at = self._expires.get(key)
        return expire_at is not None and expire_at <= self.now()

    def ttl(self, key):
        """키의 남은 만료 시간 반환 및 미설정 시 -1 반환"""

        expire_at = self._expires.get(key)
        if expire_at is None:
            return -1

        remaining = int(expire_at - self.now())
        if remaining < 0:
            return 0
        return remaining

    def pop_expired_key(self):
        """힙의 오래된 기록을 제외한 현재 만료 키 반환"""

        current_time = self.now()

        while not self._heap.is_empty():
            expire_at, key = self._heap.peek()
            if expire_at > current_time:
                return None

            self._heap.pop()
            latest_expire_at = self._expires.get(key)
            # TTL 변경 시 힙에 남은 이전 기록은 최신 만료 시각과 다르면 무시
            if latest_expire_at == expire_at:
                return key

        return None
