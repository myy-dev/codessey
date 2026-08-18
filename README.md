# Mini Redis 구축

## 프로젝트 개요 (Project Overview)

- Redis의 핵심 동작을 학습하기 위해 순수 Python으로 구현한 CLI 기반 Mini Redis입니다.
- String 저장소 외에 학습용 이진 트리, BST, 단일 프로세스 Pub/Sub를 포함합니다.

## 실행 환경 (Environment)

- **언어**: Python 3.8 이상
- **외부 의존성**: 없음(Python 표준 라이브러리만 사용)

## 실행 및 테스트 (Run & Test)

```bash
# CLI 실행
python3 main.py

# 전체 단위 테스트 실행
python3 -m unittest discover -v
```

CLI에서 `exit` 또는 `quit`을 입력하면 종료됩니다.

## 프로젝트 구조 (Project Structure)

```text
.
├── main.py                 # CLI REPL 진입점
├── parser.py               # 따옴표 입력을 지원하는 명령어 파서
├── response.py             # Redis 스타일 응답 생성
├── store.py                # 명령 실행 및 저장소 정책 조정
├── memory.py               # 메모리 사용량과 eviction 통계
├── ttl.py                  # TTL 해시맵과 최소 힙 관리
├── pubsub.py               # 채널과 구독자별 메시지 버퍼
├── data_structures/
│   ├── binary_tree.py      # 일반 이진 트리와 4종 순회
│   ├── binary_search_tree.py # BST 삽입, 검색, 삭제, 정렬 순회
│   ├── dynamic_array.py    # 동적 배열
│   ├── hash_map.py         # 체이닝 해시맵
│   ├── linked_list.py      # 이중 연결 리스트
│   └── min_heap.py         # TTL용 최소 힙
├── STACK_QUEUE_DEQUE.md    # 스택, 큐, 덱 학습 정리
├── tests/                  # 단위 및 통합 회귀 테스트
└── docs/                   # 단계별 학습 노트와 구현 계획
```

## 수행 항목 체크리스트

모든 기본 및 보너스 항목의 구현과 문서화를 완료했습니다.

### 기본 자료구조 직접 구현

#### 이중 연결 리스트

- [x] 노드에 `prev`, `next`, `data` 필드 포함
- [x] `insert_front`, `insert_back` 구현
- [x] `remove_front`, `remove_back`, `remove_node` 구현
- [x] `move_to_front` 구현
- [x] 삽입, 삭제, 이동 연산 O(1) 보장

#### 해시맵

- [x] 직접 설계한 해시 함수 구현
- [x] 체이닝 방식 충돌 해결 구현
- [x] `put`, `get`, `remove`, `contains`, `keys`, `size` 구현
- [x] 로드 팩터 0.75 초과 시 버킷 2배 확장

#### 최소 힙

- [x] `push`, `pop`, `peek`, `size` 구현
- [x] `_heapify_up`, `_heapify_down` 구현
- [x] TTL 만료 관리용 `(expire_at, key)` 형태 요소 처리

### String 타입 명령어

#### 공통 규칙

- [x] 키 기반 명령어 실행 전 만료 여부 확인
- [x] 만료된 키는 '없는 키'처럼 처리
- [x] Redis 스타일 출력 형식 적용 (`OK`, `(nil)`, `(integer) N`, `(error) ...`)

#### `SET key value`

- [x] 키에 값 저장
- [x] 성공 시 `OK` 반환
- [x] 성공 시 LRU 추적 업데이트
- [x] 메모리 초과 시, 만료 키 정리 후 LRU 제거 수행
- [x] 기존 키 덮어쓰기 시 기존 TTL 초기화

#### `GET key`

- [x] 키가 없거나 만료된 경우 `(nil)` 반환
- [x] 값이 존재하면 `"value"` 형태로 반환
- [x] 반환 성공 시에만 LRU 갱신

#### `DEL key`

- [x] 삭제 성공 시 `(integer) 1` 반환
- [x] 키가 없으면 `(integer) 0` 반환
- [x] 데이터, TTL, LRU 구조에서 엔트리 함께 제거

#### `EXISTS key`

- [x] 키 존재 여부를 `(integer) 1` 또는 `(integer) 0`으로 반환

#### `DBSIZE`

- [x] 현재 저장된 키 개수를 `(integer) N`으로 반환

#### `KEYS`

- [x] 전체 키 목록을 배열 형태로 출력
- [x] 키 없으면 (empty array) 같은 형태 표현 가능

### 메모리 관리 및 LRU 자동 제거

#### `CONFIG SET maxmemory bytes`

- [x] 최대 메모리 제한 설정(byte 단위)
- [x] `bytes`는 0 이상의 정수로 검증
- [x] `0`은 메모리 무제한으로 처리
- [x] 성공 시 OK, 정수 파싱 실패 시 에러 표준 출력

#### `INFO memory`

- [x] 현재 메모리 사용량(`used_memory:<number>`) 출력
- [x] 최대 메모리 제한(`maxmemory:<number>`) 출력
- [x] 제거된 키 개수(`evicted_keys:<number>`) 출력

#### 메모리 계산 및 제거 정책

- [x] `used_memory = sum(len(utf8(key)) + len(utf8(value)))` 기준 적용
- [x] `maxmemory > 0`이고 SET 이후 메모리 초과 시 LRU 키부터 제거
- [x] 제거된 키 수를 `evicted_keys`에 누적
- [x] 단일 엔트리(키 + 값)가 `maxmemory`를 초과하면 저장하지 않고 OOM 에러 반환

### TTL 관리

#### `EXPIRE key seconds`

- [x] 키의 만료 시간 설정(초 단위)
- [x] 키가 없으면 `(integer) 0` 반환
- [x] `seconds <= 0`이면 즉시 만료 처리(존재 시 삭제 후 `(integer) 1` 반환)
- [x] 정상 설정 시 `(integer) 1` 반환

#### `TTL key`

- [x] 키의 남은 만료 시간 조회
- [x] 키가 없으면 `(integer) -2` 반환
- [x] 키는 존재하지만 만료 시간이 없으면 `(integer) -1` 반환
- [x] 만료 시간이 있으면 남은 초를 `(integer) N`으로 반환

#### 만료 처리 정책

- [x] 힙 기반으로 가장 빠른 만료 키 확인
- [x] lazy deletion 방식으로 오래된 만료 힙 레코드 무시
- [x] 만료된 키는 GET 시 삭제 후 `(nil)` 반환
- [x] 만료로 삭제된 키는 LRU 갱신하지 않음

### CLI 인터페이스 및 에러 처리

#### CLI REPL

- [x] `mini-redis>` 프롬프트 출력
- [x] 사용자 입력 반복 처리
- [x] 명령어 파싱, 실행, 결과 출력 흐름 구현
- [x] `exit` 또는 `quit` 입력 시 종료

#### 에러 처리

- [x] 알 수 없는 명령 에러 처리: `(error) ERR unknown command '<cmd>'`
- [x] 인자 개수 오류 처리: `(error) ERR wrong number of arguments for '<cmd>' command`
- [x] 정수 파싱 실패 처리: `(error) ERR value is not an integer or out of range`
- [x] OOM 에러 처리: `(error) OOM command not allowed when used_memory > 'maxmemory'`

#### 값 파싱

- [x] 공백 없는 값 입력 지원
- [x] 큰따옴표로 감싼 값과 escape된 따옴표 입력 지원

### 코드 구조

#### 모듈 분리

- [x] 각 자료구조를 독립 모듈 또는 파일로 분리
- [x] 핵심 클래스와 함수에 주석 또는 docstring 작성

#### 로직 분리

- [x] 명령어 파싱 로직과 실행 로직 분리
- [x] 저장소, LRU, TTL, 메모리 사용량 갱신 흐름을 명확히 분리

### 보너스 과제

#### 동적 배열 직접 구현

##### 기본 연산

- [x] `append`, `get`, `set`, `remove` 구현

##### 확장 로직

- [x] capacity 2배 확장 로직 구현
- [x] 최소 힙 내부 저장소에 동적 배열 적용

#### 스택/큐/덱 이해와 활용

##### 개념 조사

- [x] 스택, 큐, 덱 개념 조사

##### 문서화

- [x] `STACK_QUEUE_DEQUE.md` 문서 작성

#### 이진 트리와 순회 알고리즘

##### 트리 구현

- [x] 이진 트리 구현

##### 순회 알고리즘

- [x] 전위, 중위, 후위, 레벨 순회 구현

##### 힙 연계 학습

- [x] 힙을 완전 이진 트리의 배열 표현 관점에서 설명 (`docs/STEP1_STUDY_NOTES.md`)

#### 이진 탐색 트리(BST)

##### BST 기본 연산

- [x] 삽입, 탐색, 삭제 구현

##### 정렬 결과

- [x] 중위 순회 정렬 결과 구현

#### Pub/Sub 기능 구현

##### 명령어

- [x] `PUBLISH`, `SUBSCRIBE` 명령어 구현

##### 메시징 구조

- [x] 채널 기반 메시징 구현
- [x] 연결 리스트를 메시지 큐 또는 구독자별 버퍼로 재활용

### 제약 사항 (Constraints)

#### 내장 자료형 제한

- `dict`, `set`, `collections` 사용 금지
- 내장 컬렉션으로 해시맵 또는 캐시 대체 금지

#### 기능 범위

- 네트워크 통신 미구현
- 데이터 영속성 미구현
- Redis 복합 자료형(List, Set, Sorted Set 등) 미구현
- 멀티스레딩 및 락 기반 동시성 처리 미구현

#### 출력 및 메모리 계산

- Redis 스타일 응답 형식 유지
- 자료구조 오버헤드는 제외하고 키와 값의 UTF-8 길이만 계산

### 명령어 명세 (Command Specification)

| 명령어                       | 설명                  | 성공 출력                                     |
| ---------------------------- | --------------------- | --------------------------------------------- |
| `SET key value`              | 키에 값 저장          | `OK`                                          |
| `GET key`                    | 키의 값 조회          | `"value"` 또는 `(nil)`                        |
| `DEL key`                    | 키 삭제               | `(integer) 1` 또는 `(integer) 0`              |
| `EXISTS key`                 | 키 존재 여부 확인     | `(integer) 1` 또는 `(integer) 0`              |
| `DBSIZE`                     | 전체 키 개수 조회     | `(integer) N`                                 |
| `KEYS`                       | 전체 키 목록 출력     | 배열 형태                                     |
| `CONFIG SET maxmemory bytes` | 최대 메모리 제한 설정 | `OK`                                          |
| `INFO memory`                | 메모리 정보 조회      | `used_memory`, `maxmemory`, `evicted_keys`    |
| `EXPIRE key seconds`         | TTL 설정              | `(integer) 1` 또는 `(integer) 0`              |
| `TTL key`                    | 남은 TTL 조회         | `(integer) N`, `(integer) -1`, `(integer) -2` |
| `SUBSCRIBE channel`          | 채널 구독             | 구독 확인 배열                                |
| `PUBLISH channel message`    | 메시지 발행           | 메시지를 받은 구독자 수                       |

### 단일 프로세스 Pub/Sub 사용

네트워크 통신 없이 여러 저장소 인스턴스가 하나의 `PubSubManager`를 공유합니다. `PUBLISH`는 각 구독자의 연결 리스트 버퍼에 메시지를 넣고, `read_messages`는 발행 순서대로 버퍼를 비웁니다.

```python
from pubsub import PubSubManager
from store import MiniRedisStore

bus = PubSubManager()
subscriber = MiniRedisStore(pubsub_manager=bus, subscriber_id="client-1")
publisher = MiniRedisStore(pubsub_manager=bus)

subscriber.execute(["SUBSCRIBE", "news"])
publisher.execute(["PUBLISH", "news", "hello"])
assert subscriber.read_messages("news") == ["hello"]
```

Pub/Sub 버퍼는 키-값 데이터가 아니므로 `used_memory`와 LRU 정책의 대상에 포함하지 않습니다.
