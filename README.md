# Mini Redis 구축

## 프로젝트 개요 (Project Overview)

Redis의 핵심 동작을 학습하기 위해 순수 Python으로 구현한 CLI 기반 Mini Redis

## 프로젝트 구조 (Project Structure)

```text
.
├── main.py                 # 기존 CLI 실행 경로 호환 래퍼
├── mini_redis/
│   ├── __init__.py         # 애플리케이션 패키지
│   ├── __main__.py         # 모듈 실행 진입점
│   ├── cli.py              # CLI REPL
│   ├── parser.py           # 명령어 파서
│   ├── response.py         # Redis 스타일 응답 생성
│   ├── store.py            # 명령 실행 및 저장소 정책 조정
│   ├── memory.py           # 메모리와 eviction 통계
│   ├── ttl.py              # TTL 관리
│   └── pubsub.py           # 채널과 구독자별 메시지 버퍼
├── data_structures/
│   ├── binary_tree.py      # 일반 이진 트리와 4종 순회
│   ├── binary_search_tree.py # BST 삽입, 검색, 삭제, 정렬 순회
│   ├── dynamic_array.py    # 동적 배열
│   ├── hash_map.py         # 체이닝 해시맵
│   ├── linked_list.py      # 이중 연결 리스트
│   └── min_heap.py         # TTL용 최소 힙
├── tests/                  # 단위 및 통합 회귀 테스트
└── docs/
    ├── USER_GUIDE.md        # 명령어 명세 및 Pub/Sub 사용 안내
    ├── USER_DEMO.md         # 실행 예제 및 예상 출력
    └── STACK_QUEUE_DEQUE.md # 스택, 큐, 덱 및 힙 학습 정리
```

## 수행 항목 체크리스트

### 저장소 자료구조

- [x] 이중 연결 리스트: `prev`, `next`, `data` 노드 필드와 `insert_front`, `insert_back`, `remove_front`, `remove_back`, `remove_node`, `move_to_front` 연산 구현
- [x] 이중 연결 리스트의 삽입, 삭제, 이동 연산 O(1) 보장
- [x] 해시맵: 직접 설계한 해시 함수와 체이닝 방식 충돌 해결 구현
- [x] 해시맵의 `put`, `get`, `remove`, `contains`, `keys`, `size` 연산 구현
- [x] 해시맵 로드 팩터 0.75 초과 시 버킷 2배 확장
- [x] 최소 힙: `push`, `pop`, `peek`, `size`, `_heapify_up`, `_heapify_down` 연산 구현
- [x] TTL 만료 관리를 위한 `(expire_at, key)` 요소 처리

### String 타입 명령어

- [x] 키 기반 명령어 실행 전 만료 여부 확인, 만료 키를 없는 키처럼 처리
- [x] Redis 스타일 출력 형식 적용 (`OK`, `(nil)`, `(integer) N`, `(error) ...`)
- [x] `SET key value`: 값 저장, 성공 시 `OK` 반환, LRU 추적 갱신
- [x] `SET`: 메모리 초과 시 만료 키 정리 후 LRU 제거, 기존 키 덮어쓰기 시 TTL 초기화
- [x] `GET key`: 키가 없거나 만료된 경우 `(nil)`, 값이 있으면 `"value"` 반환
- [x] `GET`: 조회 성공 시에만 LRU 갱신
- [x] `DEL key`: 삭제 성공 시 `(integer) 1`, 키가 없으면 `(integer) 0` 반환
- [x] `DEL`: 데이터, TTL, LRU 구조에서 해당 엔트리 함께 제거
- [x] `EXISTS key`: 키 존재 여부를 `(integer) 1` 또는 `(integer) 0`으로 반환
- [x] `DBSIZE`: 현재 저장된 키 개수를 `(integer) N`으로 반환
- [x] `KEYS`: 전체 키를 배열 형태로 출력하고, 키가 없으면 `(empty array)` 반환

### 메모리 관리 및 LRU 자동 제거

- [x] `CONFIG SET maxmemory bytes`: byte 단위 최대 메모리 제한 설정 및 0 이상 정수 검증
- [x] `CONFIG SET`: `0`을 메모리 무제한으로 처리하고 성공 시 `OK` 반환
- [x] `CONFIG SET`: 정수 파싱 실패 시 오류 반환
- [x] `INFO memory`: `used_memory:<number>`, `maxmemory:<number>`, `evicted_keys:<number>` 출력
- [x] `used_memory = sum(len(utf8(key)) + len(utf8(value)))` 기준 적용
- [x] `maxmemory > 0`이고 SET 이후 메모리 초과 시 LRU 키부터 제거
- [x] 제거된 키 수를 `evicted_keys`에 누적
- [x] 단일 엔트리(키 + 값)가 `maxmemory`를 초과하면 저장하지 않고 OOM 에러 반환

### TTL 관리

- [x] `EXPIRE key seconds`: 초 단위 만료 시간 설정, 키가 없으면 `(integer) 0` 반환
- [x] `EXPIRE`: `seconds <= 0`이면 키를 즉시 삭제하고 `(integer) 1` 반환, 정상 설정도 `(integer) 1` 반환
- [x] `TTL key`: 키가 없으면 `(integer) -2`, 만료 시간이 없으면 `(integer) -1` 반환
- [x] `TTL`: 만료 시간이 있으면 남은 초를 `(integer) N`으로 반환
- [x] 힙 기반으로 가장 빠른 만료 키 확인
- [x] lazy deletion 방식으로 오래된 만료 힙 레코드 무시
- [x] 만료된 키는 GET 시 삭제 후 `(nil)` 반환
- [x] 만료로 삭제된 키는 LRU 갱신하지 않음

### CLI와 입력 및 오류 처리

- [x] `mini-redis>` 프롬프트 기반 사용자 입력 반복, 명령어 파싱·실행·결과 출력
- [x] `exit` 또는 `quit` 입력 시 CLI 종료
- [x] 알 수 없는 명령 오류: `(error) ERR unknown command '<cmd>'`
- [x] 인자 개수 오류: `(error) ERR wrong number of arguments for '<cmd>' command`
- [x] 정수 파싱 오류: `(error) ERR value is not an integer or out of range`
- [x] 메모리 초과 오류: `(error) OOM command not allowed when used_memory > 'maxmemory'`
- [x] 공백 없는 값, 큰따옴표로 감싼 값, escape된 따옴표 입력 지원

### 모듈과 로직 분리

- [x] 자료구조별 독립 모듈 또는 파일 구성
- [x] 핵심 클래스와 함수에 주석 또는 docstring 작성
- [x] 명령어 파싱 로직과 실행 로직 분리
- [x] 저장소, LRU, TTL, 메모리 사용량 갱신 책임 분리

### 보너스 자료구조와 기능

- [x] 동적 배열: `append`, `get`, `set`, `remove` 연산과 capacity 2배 확장 구현
- [x] 최소 힙 내부 저장소에 동적 배열 적용
- [x] 스택, 큐, 덱 개념 조사 및 `docs/STACK_QUEUE_DEQUE.md` 문서 작성
- [x] 이진 트리 및 전위·중위·후위·레벨 순회 구현
- [x] 힙의 완전 이진 트리 배열 표현을 `docs/STACK_QUEUE_DEQUE.md`에 설명
- [x] 이진 탐색 트리 삽입·탐색·삭제와 중위 순회 정렬 결과 구현
- [x] `PUBLISH`, `SUBSCRIBE` 명령어 및 채널 기반 메시징 구현
- [x] 연결 리스트를 메시지 큐 또는 구독자별 버퍼로 재활용

## 제약 사항 (Constraints)

- `dict`, `set`, `collections` 사용 금지
- 내장 컬렉션으로 해시맵 또는 캐시 대체 금지
- 네트워크 통신 미구현
- 데이터 영속성 미구현
- Redis 복합 자료형(List, Set, Sorted Set 등) 미구현
- 멀티스레딩 및 락 기반 동시성 처리 미구현
- Redis 스타일 응답 형식 유지
- 자료구조 오버헤드는 제외하고 키와 값의 UTF-8 길이만 계산

## 결과물 (Deliverables)

### 사용자 가이드 (User Guide)

- [USER_GUIDE.md](docs/USER_GUIDE.md)
- [USER_DEMO.md](docs/USER_DEMO.md)
