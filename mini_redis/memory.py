class MemoryManager:
    """payload 메모리, maxmemory 설정값, LRU eviction 횟수 추적"""

    def __init__(self):
        """메모리 사용량, 최대 메모리, 제거된 키 수 초기화"""

        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0

    def entry_size(self, key, value):
        """키와 값의 UTF-8 바이트 길이를 합산한 엔트리 크기 계산"""

        return len(str(key).encode("utf-8")) + len(str(value).encode("utf-8"))

    def set_maxmemory(self, value):
        """허용할 최대 메모리 크기의 바이트 단위 설정"""

        self.maxmemory = value

    def is_limited(self):
        """최대 메모리 사용량 제한의 활성화 여부 확인"""

        return self.maxmemory > 0

    def can_store_entry(self, key, value):
        """단일 엔트리의 최대 메모리 제한 충족 여부 확인"""

        if not self.is_limited():
            return True
        return self.entry_size(key, value) <= self.maxmemory

    def add_entry(self, key, value):
        """새 엔트리 크기의 현재 메모리 사용량 반영"""

        self.used_memory += self.entry_size(key, value)

    def replace_entry(self, key, old_value, new_value):
        """기존 값과 새 값의 크기 차이를 현재 메모리 사용량에 반영"""

        self.used_memory += self.entry_size(key, new_value) - self.entry_size(
            key, old_value
        )

    def remove_entry(self, key, value):
        """삭제한 엔트리 크기의 현재 메모리 사용량 차감"""

        self.used_memory -= self.entry_size(key, value)
        if self.used_memory < 0:
            self.used_memory = 0

    def over_limit(self):
        """현재 메모리 사용량의 활성화된 최대 메모리 초과 여부 확인"""

        return self.is_limited() and self.used_memory > self.maxmemory

    def record_eviction(self):
        """메모리 제한으로 제거된 키 수 증가"""

        self.evicted_keys += 1
