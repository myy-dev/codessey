class HashMapEntry:
    """체이닝 방식의 키, 값, 다음 엔트리 보관"""

    def __init__(self, key, value):
        """키와 값 저장 및 다음 엔트리 연결 초기화"""

        self.key = key
        self.value = value
        self.next = None


class HashMap:
    """체이닝 방식과 명시적 resize 제어를 사용하는 HashMap"""

    def __init__(self, initial_capacity=8, max_load_factor=0.75):
        """초기 버킷 용량과 최대 적재율 검증 및 저장 공간 초기화"""

        if initial_capacity <= 0:
            raise ValueError("초기 capacity 양수 조건 위반")
        if max_load_factor <= 0:
            raise ValueError("최대 load factor 양수 조건 위반")
        self._capacity = initial_capacity
        self._max_load_factor = max_load_factor
        self._size = 0
        self._buckets = [None] * self._capacity

    def put(self, key, value):
        """키와 값 추가 또는 기존 값 갱신 및 필요 시 버킷 확장"""

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
        """키에 대응하는 값 또는 기본값 반환"""

        entry = self._find_entry(key)
        if entry is None:
            return default
        return entry.value

    def remove(self, key):
        """키에 대응하는 엔트리 제거 및 기존 값 반환"""

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
        """키에 대응하는 엔트리의 존재 여부 확인"""

        return self._find_entry(key) is not None

    def keys(self):
        """모든 버킷에 저장된 키 목록 반환"""

        result = []
        for i in range(self._capacity):
            current = self._buckets[i]
            while current is not None:
                result.append(current.key)
                current = current.next
        return result

    def size(self):
        """저장된 엔트리 개수 반환"""

        return self._size

    def capacity(self):
        """현재 버킷 용량 반환"""

        return self._capacity

    def _hash(self, key):
        """문자열 변환된 키의 31 기반 해시값 계산"""

        text = str(key)
        hash_value = 0
        for char in text:
            hash_value = (hash_value * 31 + ord(char)) & 0x7FFFFFFF
        return hash_value

    def _bucket_index(self, key):
        """키의 해시값에 대응하는 버킷 인덱스 계산"""

        return self._hash(key) % self._capacity

    def _find_entry(self, key):
        """체이닝된 버킷에서 키에 대응하는 엔트리 탐색"""

        current = self._buckets[self._bucket_index(key)]
        while current is not None:
            if current.key == key:
                return current
            current = current.next
        return None

    def _load_factor(self):
        """현재 버킷 용량 대비 엔트리 적재율 계산"""

        return self._size / self._capacity

    def _resize(self, new_capacity):
        """버킷 용량 변경 및 기존 엔트리 재배치"""

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
        """내장 len 호출을 위한 엔트리 개수 반환"""

        return self._size
