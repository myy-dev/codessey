class DynamicArray:
    """명시적 capacity 확장을 지원하는 소형 DynamicArray"""

    def __init__(self, initial_capacity=4):
        """초기 용량 검증 및 요소 저장 공간 초기화"""

        if initial_capacity <= 0:
            raise ValueError("초기 capacity 양수 조건 위반")
        self._capacity = initial_capacity
        self._size = 0
        self._items = [None] * self._capacity

    def append(self, value):
        """배열 끝에 값 추가 및 공간 부족 시 용량 확장"""

        if self._size == self._capacity:
            self._resize(self._capacity * 2)
        self._items[self._size] = value
        self._size += 1

    def get(self, index):
        """유효한 인덱스에 저장된 값 반환"""

        self._validate_index(index)
        return self._items[index]

    def set(self, index, value):
        """유효한 인덱스의 저장값 변경"""

        self._validate_index(index)
        self._items[index] = value

    def remove(self, index):
        """지정 인덱스의 값 제거 및 뒤쪽 요소의 앞 이동"""

        self._validate_index(index)
        value = self._items[index]
        for i in range(index, self._size - 1):
            self._items[i] = self._items[i + 1]
        self._size -= 1
        self._items[self._size] = None
        return value

    def pop(self):
        """배열 마지막 값 제거 및 반환"""

        if self._size == 0:
            raise IndexError("빈 배열 pop 요청")
        return self.remove(self._size - 1)

    def size(self):
        """현재 저장된 요소 개수 반환"""

        return self._size

    def capacity(self):
        """현재 요소 저장 공간의 용량 반환"""

        return self._capacity

    def is_empty(self):
        """배열의 빈 상태 여부 확인"""

        return self._size == 0

    def to_list(self):
        """저장된 요소의 내장 리스트 변환"""

        return list(self)

    def _resize(self, new_capacity):
        """새 용량의 저장 공간 할당 및 기존 요소 복사"""

        new_items = [None] * new_capacity
        for i in range(self._size):
            new_items[i] = self._items[i]
        self._items = new_items
        self._capacity = new_capacity

    def _validate_index(self, index):
        """인덱스의 현재 요소 범위 포함 여부 검증"""

        if index < 0 or index >= self._size:
            raise IndexError("배열 인덱스 범위 초과")

    def __len__(self):
        """내장 len 호출을 위한 요소 개수 반환"""

        return self._size

    def __iter__(self):
        """첫 인덱스부터 마지막 저장 요소까지 순회"""

        for i in range(self._size):
            yield self._items[i]
