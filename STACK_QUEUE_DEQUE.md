# 스택, 큐, 덱 학습 정리

## 핵심 비교

| 자료구조 | 데이터 규칙 | 대표 연산 | 양 끝 연산 복잡도 | 주요 사용 사례 |
| --- | --- | --- | --- | --- |
| 스택(Stack) | LIFO, 마지막 입력이 먼저 출력 | `push`, `pop`, `peek` | 한쪽 끝에서 O(1) | DFS, 실행 취소, 파서 상태 |
| 큐(Queue) | FIFO, 첫 입력이 먼저 출력 | `enqueue`, `dequeue`, `front` | 앞/뒤를 관리하면 O(1) | BFS, 작업 대기열, 메시지 버퍼 |
| 덱(Deque) | 양쪽에서 삽입·삭제 | `push_front`, `push_back`, `pop_front`, `pop_back` | 양쪽 모두 O(1) | LRU, 슬라이딩 윈도우, 양방향 작업 큐 |

## 스택

스택은 한쪽 끝인 top에서만 데이터를 넣고 꺼낸다. 호출 스택처럼 가장 최근 상태를 먼저 복원해야 하는 문제와, 이진 트리의 깊이 우선 순회를 반복문으로 구현할 때 적합하다.

- `push(value)`: top에 추가
- `pop()`: top 값을 제거하고 반환
- `peek()`: 제거하지 않고 top 확인
- `is_empty()`: 비어 있는지 확인

동적 배열을 사용하면 끝 삽입과 삭제는 평균 O(1)이다. 연결 리스트의 front를 top으로 사용해도 각 연산을 O(1)에 처리할 수 있다.

## 큐

큐는 rear로 들어온 값이 front에서 입력 순서대로 나간다. 이 프로젝트의 `BinaryTree.level_order`는 이중 연결 리스트의 back에 노드를 넣고 front에서 꺼내는 큐로 레벨 순회를 수행한다.

- `enqueue(value)`: rear에 추가
- `dequeue()`: front 값을 제거하고 반환
- `front()`: 다음 출력 값 확인
- `is_empty()`: 비어 있는지 확인

Python 리스트의 첫 요소를 매번 삭제하면 뒤 원소를 이동해야 하므로 O(n)이다. front와 rear를 가진 연결 리스트를 사용하면 입력과 출력 모두 O(1)이다.

## 덱

덱은 front와 back 양쪽에서 데이터를 추가하고 제거할 수 있다. 이 프로젝트의 `DoublyLinkedList`가 덱의 기반 연산을 제공한다.

- `insert_front`, `remove_front`
- `insert_back`, `remove_back`

Mini Redis의 LRU는 가장 최근 사용 키를 front로 이동하고, 메모리 제한을 넘으면 가장 오래된 tail을 제거한다. 따라서 LRU 연결 리스트는 덱의 양쪽 끝 연산을 실제 정책에 활용한 사례다.

## Pub/Sub 메시지 버퍼와의 연결

`PubSubManager`는 채널별 구독자를 관리하고, 각 구독자에게 `DoublyLinkedList` 메시지 버퍼를 부여한다. `PUBLISH`는 버퍼의 back에 메시지를 추가하고, 소비자는 front에서 메시지를 제거한다. 따라서 메시지가 발행 순서대로 전달되는 FIFO 큐가 된다.

네트워크와 비동기 처리는 과제 범위 밖이므로 여러 `MiniRedisStore` 인스턴스가 하나의 인메모리 `PubSubManager`를 공유하는 학습 모델을 사용한다.
