from .dynamic_array import DynamicArray


class MinHeap:
    """DynamicArray 기반 MinHeap"""

    def __init__(self):
        """힙 요소 저장용 동적 배열 초기화"""

        self._items = DynamicArray()

    def push(self, value):
        """새 값 추가 및 상향 이동을 통한 최소 힙 조건 복구"""

        self._items.append(value)
        self._heapify_up(self._items.size() - 1)

    def pop(self):
        """최솟값 제거 및 하향 이동을 통한 최소 힙 조건 복구"""

        if self.size() == 0:
            return None

        root = self._items.get(0)
        last = self._items.pop()
        if self.size() > 0:
            self._items.set(0, last)
            self._heapify_down(0)
        return root

    def peek(self):
        """최솟값의 제거 없는 조회"""

        if self.size() == 0:
            return None
        return self._items.get(0)

    def size(self):
        """현재 힙 요소 개수 반환"""

        return self._items.size()

    def is_empty(self):
        """힙의 빈 상태 여부 확인"""

        return self.size() == 0

    def to_list(self):
        """내부 힙 배열의 내장 리스트 변환"""

        return self._items.to_list()

    def _heapify_up(self, index):
        """지정 요소의 부모 방향 이동을 통한 최소 힙 조건 복구"""

        while index > 0:
            parent = (index - 1) // 2
            if self._items.get(parent) <= self._items.get(index):
                break
            self._swap(parent, index)
            index = parent

    def _heapify_down(self, index):
        """지정 요소의 자식 방향 이동을 통한 최소 힙 조건 복구"""

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
        """두 인덱스에 저장된 힙 요소 교환"""

        temp = self._items.get(left)
        self._items.set(left, self._items.get(right))
        self._items.set(right, temp)

    def __len__(self):
        """내장 len 호출을 위한 힙 요소 개수 반환"""

        return self.size()
