# Mini Redis 구현 계획

## 1. 프로젝트 개요

이 프로젝트는 Redis의 핵심 동작을 학습하기 위해 순수 Python 3.8 이상으로 구현하는 CLI 기반 Mini Redis이다.

주요 목표는 다음과 같다.

- 내장 `dict`, `set`, `collections` 없이 핵심 자료구조를 직접 구현한다.
- String 타입 중심의 Redis 명령어를 지원한다.
- TTL, LRU eviction, maxmemory 제한을 직접 설계한다.
- Redis 스타일 응답 형식과 CLI REPL 흐름을 구현한다.
- 일반 이진 트리, BST, 단일 프로세스 Pub/Sub 보너스를 독립 모듈로 구현한다.

## 2. 프로젝트 구조

### 2.1 현재 구조

현재 저장소는 기본 기능과 보너스 확장, 단계별 학습 문서를 포함한다.

```text
.
├── main.py
├── parser.py
├── response.py
├── store.py
├── memory.py
├── ttl.py
├── pubsub.py
├── STACK_QUEUE_DEQUE.md
├── data_structures/
│   ├── __init__.py
│   ├── binary_tree.py
│   ├── binary_search_tree.py
│   ├── dynamic_array.py
│   ├── linked_list.py
│   ├── hash_map.py
│   └── min_heap.py
├── tests/
│   ├── __init__.py
│   ├── test_data_structures.py
│   ├── test_commands.py
│   ├── test_trees.py
│   └── test_pubsub.py
├── docs/
│   ├── plan.md
│   ├── STEP1_STUDY_NOTES.md
│   ├── STEP2_STUDY_NOTES.md
│   ├── STEP3_STUDY_NOTES.md
│   ├── STEP4_STUDY_NOTES.md
│   ├── STEP5_STUDY_NOTES.md
│   ├── STEP6_STUDY_NOTES.md
│   ├── STEP7_STUDY_NOTES.md
│   └── STEP8_STUDY_NOTES.md
├── README.md
└── .gitignore
```

- `README.md`: 프로젝트 요구사항과 체크리스트
- `.gitignore`: 운영체제 및 Python 실행 산출물 제외 설정
- `main.py`: CLI REPL 진입점
- `parser.py`: 사용자 입력 파싱
- `response.py`: Redis 스타일 응답 생성
- `store.py`: 명령어 실행과 저장소 상태 관리
- `memory.py`: 메모리 제한과 eviction 통계 관리
- `ttl.py`: TTL 만료 시간과 만료 후보 관리
- `pubsub.py`: 채널, 구독자, 연결 리스트 메시지 버퍼 관리
- `STACK_QUEUE_DEQUE.md`: 선형 자료구조 개념과 프로젝트 활용 사례
- `data_structures/`: 직접 구현 자료구조
- `tests/`: 자료구조와 명령어 단위 테스트
- `docs/plan.md`: 구현 계획 문서
- `docs/STEP*_STUDY_NOTES.md`: 단계별 구현 후 면접/학습 개념 정리

### 2.2 권장 구현 구조

기능별 책임은 현재 구조를 기준으로 유지한다. 명령어 범위가 늘어나면 테스트 파일만 기능별로 추가 분리한다.

```text
.
├── main.py
├── parser.py
├── response.py
├── store.py
├── memory.py
├── ttl.py
├── pubsub.py
├── STACK_QUEUE_DEQUE.md
├── data_structures/
│   ├── binary_tree.py
│   ├── binary_search_tree.py
│   ├── dynamic_array.py
│   ├── linked_list.py
│   ├── hash_map.py
│   └── min_heap.py
├── tests/
│   ├── test_data_structures.py
│   ├── test_commands.py
│   ├── test_trees.py
│   └── test_pubsub.py
├── docs/
│   ├── plan.md
│   ├── STEP1_STUDY_NOTES.md
│   ├── STEP2_STUDY_NOTES.md
│   ├── STEP3_STUDY_NOTES.md
│   ├── STEP4_STUDY_NOTES.md
│   ├── STEP5_STUDY_NOTES.md
│   ├── STEP6_STUDY_NOTES.md
│   ├── STEP7_STUDY_NOTES.md
│   └── STEP8_STUDY_NOTES.md
├── README.md
└── .gitignore
```

- `main.py`: CLI REPL 진입점
- `parser.py`: 사용자 입력 파싱, 큰따옴표 문자열 처리, 인자 개수 검증
- `response.py`: Redis 스타일 응답 문자열 생성
- `store.py`: 명령어 실행, 데이터 저장소, LRU, TTL, 메모리 정책 연결
- `memory.py`: `used_memory`, `maxmemory`, `evicted_keys` 관리
- `ttl.py`: 만료 시간 저장, 만료 검사, lazy deletion 처리
- `pubsub.py`: 공유 인메모리 채널과 구독자별 FIFO 버퍼
- `data_structures/`: 직접 구현 자료구조
- `tests/`: 자료구조와 명령어 단위 테스트

## 3. 구현 단계 요약

1. 동적 배열, 이중 연결 리스트, 해시맵, 최소 힙을 먼저 구현한다.
2. 저장소 엔진에서 데이터, TTL, LRU, 메모리 사용량을 함께 관리한다.
3. Redis 스타일 응답 포맷과 명령어 파서를 구현한다.
4. String 명령어를 구현한다.
5. TTL 명령어와 만료 정책을 구현한다.
6. maxmemory와 LRU eviction을 구현한다.
7. CLI REPL과 에러 처리를 통합한다.
8. 스택·큐·덱 문서, 일반 이진 트리, BST, 단일 프로세스 Pub/Sub 보너스를 구현한다.

## 4. 자료구조 구현 계획

### 4.1 동적 배열

보너스 과제의 동적 배열은 기본 과제에 적용한다. 최소 힙의 내부 저장소로 사용하고, 해시맵 버킷 확장 개념 설명에도 연결한다.

구현 항목:

- `append`, `get`, `set`, `remove` 구현
- 내부 capacity 관리
- capacity 초과 시 2배 확장
- 인덱스 범위 검증

검증 기준:

- append 후 순서가 유지된다.
- capacity가 꽉 차면 자동 확장된다.
- `get`, `set`, `remove`가 올바른 인덱스에 대해 동작한다.

### 4.2 이중 연결 리스트

이중 연결 리스트는 LRU 관리의 핵심 자료구조로 사용한다.

구현 항목:

- 노드에 `prev`, `next`, `data` 필드 포함
- `insert_front`, `insert_back` 구현
- `remove_front`, `remove_back`, `remove_node` 구현
- `move_to_front` 구현
- head는 가장 최근 사용 키, tail은 가장 오래된 키로 관리

검증 기준:

- 삽입, 삭제, 이동 연산이 O(1)로 동작한다.
- `SET`, `GET` 성공 시 해당 키가 front로 이동한다.
- LRU eviction 시 tail 노드의 키가 제거된다.

### 4.3 해시맵

해시맵은 데이터 저장소, TTL 맵, LRU 노드 참조 저장에 사용한다.

구현 항목:

- 직접 설계한 해시 함수 구현
- 체이닝 방식 충돌 해결
- `put`, `get`, `remove`, `contains`, `keys`, `size` 구현
- 로드 팩터가 0.75를 초과하면 버킷 수 2배 확장

검증 기준:

- 같은 버킷에 충돌한 키도 독립적으로 저장된다.
- 기존 키에 `put`하면 값이 갱신된다.
- 확장 후에도 기존 키 조회가 가능하다.

### 4.4 최소 힙

최소 힙은 TTL 만료 관리에 사용한다. 이진 트리 보너스 과제는 여기서 완전 이진 트리의 배열 표현으로 일부 통합한다.

구현 항목:

- 동적 배열 기반 저장소 사용
- `push`, `pop`, `peek`, `size` 구현
- `_heapify_up`, `_heapify_down` 구현
- `(expire_at, key)` 형태 요소 처리
- 부모/자식 인덱스 관계를 완전 이진 트리 관점으로 문서화

검증 기준:

- `peek`은 가장 이른 만료 시간을 반환한다.
- `pop`은 만료 시간이 가장 작은 요소부터 반환한다.
- 같은 키의 오래된 만료 기록은 lazy deletion으로 무시된다.

## 5. 저장소 엔진 설계

`store.py`는 Mini Redis의 핵심 실행 계층이다.

관리 상태:

- `data`: key-value 저장 해시맵
- `expires`: key-expire_at 저장 해시맵
- `expire_heap`: TTL 만료 확인용 최소 힙
- `lru_list`: 사용 순서 관리용 이중 연결 리스트
- `lru_nodes`: key-node 참조 해시맵
- `memory`: 메모리 사용량과 eviction 통계

공통 처리 흐름:

1. 키 기반 명령어 실행 전 해당 키의 만료 여부를 확인한다.
2. 만료된 키는 데이터, TTL, LRU, 메모리 상태에서 제거한다.
3. 명령어별 비즈니스 로직을 수행한다.
4. 필요한 경우 LRU 위치와 메모리 사용량을 갱신한다.
5. Redis 스타일 응답 문자열을 반환한다.

## 6. 명령어 구현 계획

### 6.1 공통 규칙

- Redis 스타일 출력 형식을 유지한다.
- 키가 만료된 경우 없는 키처럼 처리한다.
- 명령어 이름은 대소문자를 구분하지 않고 처리한다.
- 알 수 없는 명령은 `(error) ERR unknown command '<cmd>'`를 반환한다.
- 인자 개수 오류는 `(error) ERR wrong number of arguments for '<cmd>' command`를 반환한다.

### 6.2 String 명령어

#### `SET key value`

- 키에 값을 저장한다.
- 성공 시 `OK`를 반환한다.
- 기존 키를 덮어쓰면 기존 TTL을 제거한다.
- 저장 성공 시 LRU를 갱신한다.
- 저장 후 maxmemory를 초과하면 LRU 순서대로 제거한다.
- 단일 엔트리 크기가 maxmemory를 초과하면 저장하지 않고 OOM 에러를 반환한다.

#### `GET key`

- 키가 없거나 만료되었으면 `(nil)`을 반환한다.
- 값이 있으면 `"value"` 형태로 반환한다.
- 조회 성공 시에만 LRU를 갱신한다.

#### `DEL key`

- 키가 있으면 데이터, TTL, LRU, 메모리 상태에서 제거하고 `(integer) 1`을 반환한다.
- 키가 없으면 `(integer) 0`을 반환한다.

#### `EXISTS key`

- 키가 존재하고 만료되지 않았으면 `(integer) 1`을 반환한다.
- 없거나 만료되었으면 `(integer) 0`을 반환한다.

#### `DBSIZE`

- 현재 저장된 키 개수를 `(integer) N`으로 반환한다.
- 조회 전 만료된 키를 정리한다.

#### `KEYS`

- 현재 저장된 키 목록을 배열 형태로 반환한다.
- 키가 없으면 empty array 형태로 출력한다.
- 정렬 요구사항은 없으므로 해시맵의 현재 키 순서를 사용한다.

### 6.3 메모리 명령어

#### `CONFIG SET maxmemory bytes`

- `bytes`를 0 이상의 정수로 검증한다.
- `0`은 메모리 무제한으로 처리한다.
- 성공 시 `OK`를 반환한다.
- 정수 파싱 실패 시 `(error) ERR value is not an integer or out of range`를 반환한다.
- maxmemory 축소 후 현재 사용량이 제한을 넘으면 LRU eviction을 수행한다.

#### `INFO memory`

다음 값을 줄 단위로 반환한다.

```text
used_memory:<number>
maxmemory:<number>
evicted_keys:<number>
```

### 6.4 TTL 명령어

#### `EXPIRE key seconds`

- 키가 없으면 `(integer) 0`을 반환한다.
- `seconds`가 정수가 아니면 정수 파싱 에러를 반환한다.
- `seconds <= 0`이면 키를 즉시 삭제하고 `(integer) 1`을 반환한다.
- 정상 설정 시 expire_at을 저장하고 최소 힙에 `(expire_at, key)`를 추가한 뒤 `(integer) 1`을 반환한다.

#### `TTL key`

- 키가 없거나 만료되었으면 `(integer) -2`를 반환한다.
- 키는 있지만 만료 시간이 없으면 `(integer) -1`을 반환한다.
- 만료 시간이 있으면 남은 초를 `(integer) N`으로 반환한다.

## 7. TTL 관리 계획

TTL은 해시맵과 최소 힙을 함께 사용한다.

- `expires` 해시맵은 key별 최신 만료 시간을 저장한다.
- `expire_heap`은 `(expire_at, key)`를 누적 저장한다.
- 같은 키에 EXPIRE가 여러 번 호출되면 힙에 오래된 기록이 남을 수 있다.
- 힙에서 꺼낸 `(expire_at, key)`가 `expires`의 최신 값과 다르면 오래된 기록으로 보고 무시한다.
- 키 기반 명령어 실행 전 해당 키를 lazy deletion으로 검사한다.
- `DBSIZE`, `KEYS`, `INFO memory`처럼 전체 상태를 보여주는 명령어 전에는 만료 가능한 키를 정리한다.

## 8. 메모리 제한과 LRU 제거 계획

### 8.1 메모리 계산

메모리 사용량은 자료구조 오버헤드를 제외하고 다음 기준으로 계산한다.

```text
used_memory = sum(len(key.encode("utf-8")) + len(value.encode("utf-8")))
```

### 8.2 LRU 정책

- `SET` 성공 시 키를 LRU front로 이동한다.
- `GET` 성공 시 키를 LRU front로 이동한다.
- `DEL`, 만료, eviction으로 제거되는 키는 LRU 구조에서도 함께 제거한다.
- maxmemory 초과 시 tail부터 제거한다.
- 제거된 키 수는 `evicted_keys`에 누적한다.

### 8.3 OOM 처리

- `maxmemory == 0`이면 제한이 없다.
- `maxmemory > 0`이고 단일 엔트리 크기가 maxmemory보다 크면 저장하지 않는다.
- 이 경우 `(error) OOM command not allowed when used_memory > 'maxmemory'`를 반환한다.

## 9. CLI, 파싱, 에러 처리

### 9.1 CLI REPL

- `mini-redis>` 프롬프트를 출력한다.
- 사용자 입력을 반복해서 읽는다.
- `exit` 또는 `quit` 입력 시 종료한다.
- 파싱, 명령 실행, 결과 출력 흐름을 분리한다.

### 9.2 값 파싱

- 공백 없는 값 입력을 지원한다.
- 큰따옴표로 감싼 값 입력을 지원한다.
- Python 표준 라이브러리 `shlex` 사용을 우선 검토한다.
- `dict`, `set`, `collections` 제한은 핵심 자료구조 대체 금지로 해석하고, 파싱용 표준 라이브러리는 허용한다.

### 9.3 에러 응답

- 알 수 없는 명령: `(error) ERR unknown command '<cmd>'`
- 인자 개수 오류: `(error) ERR wrong number of arguments for '<cmd>' command`
- 정수 파싱 실패: `(error) ERR value is not an integer or out of range`
- OOM: `(error) OOM command not allowed when used_memory > 'maxmemory'`

## 10. 보너스 과제 통합 및 확장 계획

### 10.1 기본 과제에 통합할 항목

- 동적 배열은 최소 힙 내부 저장소로 사용한다.
- 해시맵 버킷 확장 설명에 동적 배열의 capacity 확장 개념을 연결한다.
- 이진 트리 학습은 최소 힙을 완전 이진 트리의 배열 표현으로 설명해 반영한다.
- 연결 리스트는 LRU뿐 아니라 확장 Pub/Sub의 메시지 큐 또는 구독자 버퍼에도 재사용 가능하도록 설계한다.

### 10.2 독립 확장 모듈로 구현한 항목

#### 스택/큐/덱 문서화

- `STACK_QUEUE_DEQUE.md`를 별도 작성했다.
- 스택, 큐, 덱의 개념과 Redis 구현에서 연결 가능한 사례를 정리했다.

#### 이진 트리와 BST

- 일반 이진 트리 순회와 BST는 핵심 Redis String 기능에 직접 필요하지 않다.
- 기본 저장소와 분리된 학습용 모듈로 구현했다.
- 일반 트리 4종 순회와 BST 삽입, 검색, 삭제, 정렬 순회를 제공한다.

#### Pub/Sub

- `PUBLISH channel message`, `SUBSCRIBE channel` 명령어를 추가했다.
- 채널별 구독자 메시지 버퍼에 연결 리스트를 재활용했다.
- 네트워크 통신은 제외되어 있으므로 CLI 단일 프로세스 안에서 동작하는 학습용 모델로 제한한다.

## 11. 테스트 계획

### 11.1 자료구조 테스트

- 동적 배열 append, get, set, remove, capacity 확장
- 이중 연결 리스트 삽입, 삭제, 이동, tail 제거
- 해시맵 put, get, remove, contains, keys, size, 충돌 처리, 리사이징
- 최소 힙 push, pop, peek, heapify, 동일 키 TTL lazy deletion

### 11.2 명령어 테스트

- `SET`, `GET`, `DEL`, `EXISTS`, `DBSIZE`, `KEYS` 정상 동작
- 잘못된 인자 개수
- 알 수 없는 명령
- 큰따옴표 문자열 파싱

### 11.3 TTL 테스트

- `EXPIRE` 성공, 없는 키, 0 이하 seconds
- `TTL`의 `-2`, `-1`, 남은 시간 반환
- 만료된 키가 GET에서 `(nil)`로 처리되는지 확인
- 만료 삭제 시 LRU가 갱신되지 않는지 확인

### 11.4 메모리와 LRU 테스트

- `CONFIG SET maxmemory`
- `INFO memory`
- UTF-8 기준 메모리 계산
- maxmemory 초과 시 LRU tail부터 제거
- 단일 엔트리 초과 시 OOM
- `evicted_keys` 누적

### 11.5 CLI 테스트

- `mini-redis>` 프롬프트 출력
- 명령어 입력 후 응답 출력
- `exit`, `quit` 종료
- 잘못된 입력에 대한 에러 출력

### 11.6 트리와 Pub/Sub 테스트

- 일반 이진 트리의 전위, 중위, 후위, 레벨 순회
- BST 삽입, 검색, 중복 삽입, 삭제 세 경우, 정렬 순회
- 채널 중복 구독, 다중 구독자 발행 수, 구독자별 FIFO 메시지 소비
- `PUBLISH`, `SUBSCRIBE` 인자 오류

## 12. 제약 사항

- `dict`, `set`, `collections`로 해시맵, 캐시, 저장소를 대체하지 않는다.
- 네트워크 통신은 구현하지 않는다.
- 데이터 영속성은 구현하지 않는다.
- Redis 복합 자료형인 List, Set, Sorted Set 등은 구현하지 않는다.
- 멀티스레딩과 락 기반 동시성 처리는 구현하지 않는다.
- Redis 스타일 응답 형식을 유지한다.
- 메모리 계산은 키와 값의 UTF-8 길이만 사용한다.

## 13. 완료 기준

- README의 필수 체크리스트가 구현 계획에 모두 반영되어 있다.
- 기본 자료구조가 직접 구현되어 있다.
- String 명령어, TTL, 메모리 제한, LRU eviction이 동작한다.
- CLI에서 Redis 스타일 응답을 확인할 수 있다.
- 동적 배열과 힙의 이진 트리 설명이 기본 구현에 통합되어 있다.
- 스택, 큐, 덱 문서와 일반 이진 트리, BST, Pub/Sub 확장이 구현되어 있다.
- README의 모든 체크리스트 항목에 구현 또는 문서 근거가 있다.
