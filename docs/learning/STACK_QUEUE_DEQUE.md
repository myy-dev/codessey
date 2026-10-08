# 스택·큐·덱

## 핵심 비교

| 자료구조 | 데이터 규칙 | 대표 연산 | 양 끝 연산 복잡도 | 주요 사용 사례 |
| --- | --- | --- | --- | --- |
| 스택(Stack) | LIFO, 마지막 입력이 먼저 출력 | `push`, `pop`, `peek` | 한쪽 끝에서 O(1) | DFS, 실행 취소 |
| 큐(Queue) | FIFO, 첫 입력이 먼저 출력 | `enqueue`, `dequeue`, `front` | 앞/뒤를 관리하면 O(1) | BFS, 작업 대기열, 메시지 버퍼 |
| 덱(Deque) | 양쪽에서 삽입·삭제 | `push_front`, `push_back`, `pop_front`, `pop_back` | 양쪽 모두 O(1) | LRU, 슬라이딩 윈도우, 양방향 작업 큐 |

## 스택

한쪽 끝인 `top`에서만 삽입·삭제하는 LIFO 구조

호출 상태 복원과 이진 트리 깊이 우선 순회의 반복 구현에 적합

- `push(value)`: `top`에 추가
- `pop()`: `top` 값 제거 후 반환
- `peek()`: 제거 없이 `top` 값 확인
- `is_empty()`: 빈 상태 확인

동적 배열 기반 끝 삽입·삭제: 평균 O(1)

연결 리스트의 `front`를 `top`으로 사용해도 각 연산 O(1)

## 큐

`rear`로 삽입하고 `front`에서 삭제하는 FIFO 구조

이 프로젝트의 `BinaryTree.level_order`에서 이중 연결 리스트를 큐로 사용해 레벨 순회 수행

- `enqueue(value)`: `rear`에 추가
- `dequeue()`: `front` 값 제거 후 반환
- `front()`: 다음 출력 값 확인
- `is_empty()`: 빈 상태 확인

Python 리스트의 첫 요소 삭제: 나머지 원소 이동으로 O(n)

`front`와 `rear`를 보유한 연결 리스트: 삽입·삭제 모두 O(1)

## 덱

`front`와 `back` 양쪽에서 삽입·삭제를 지원하는 구조

이 프로젝트의 `DoublyLinkedList`가 양 끝 연산 제공

- `insert_front`, `remove_front`
- `insert_back`, `remove_back`

Mini Redis의 LRU: 최근 사용 키를 `front`로 이동하고 메모리 제한 초과 시 가장 오래된 `tail` 제거

덱의 양 끝 연산을 활용한 정책
