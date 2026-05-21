# Mini Redis 구축

## 프로젝트 개요 (Project Overview)

- Redis의 핵심 동작을 학습하기 위해 순수 Python으로 구현한 CLI 기반 Mini Redis입니다.

## 실행 환경 (Environment)

- **언어**: Python 3.8 이상

## 프로젝트 구조 (Project Structure)

## 수행 항목 체크리스트

### 기본 자료구조 직접 구현

#### 이중 연결 리스트

- [ ] 노드에 `prev`, `next`, `data` 필드 포함
- [ ] `insert_front`, `insert_back` 구현
- [ ] `remove_front`, `remove_back`, `remove_node` 구현
- [ ] `move_to_front` 구현
- [ ] 삽입, 삭제, 이동 연산 O(1) 보장

#### 해시맵

- [ ] 직접 설계한 해시 함수 구현
- [ ] 체이닝 방식 충돌 해결 구현
- [ ] `put`, `get`, `remove`, `contains`, `keys`, `size` 구현
- [ ] 로드 팩터 0.75 초과 시 버킷 2배 확장

#### 최소 힙

- [ ] `push`, `pop`, `peek`, `size` 구현
- [ ] `_heapify_up`, `_heapify_down` 구현
- [ ] TTL 만료 관리용 `(expire_at, key)` 형태 요소 처리

### String 타입 명령어

#### 공통 규칙

- [ ] 키 기반 명령어 실행 전 만료 여부 확인
- [ ] 만료된 키는 '없는 키'처럼 처리
- [ ] Redis 스타일 출력 형식 적용 (`OK`, `(nil)`, `(integer) N`, `(error) ...`)

#### `SET key value`

- [ ] 키에 값 저장
- [ ] 성공 시 `OK` 반환
- [ ] 성공 시 LRU 추적 업데이트
- [ ] 메모리 초과 시, LRU 제거 수행
- [ ] 기존 키 덮어쓰기 시 기존 TTL 초기화

#### `GET key`

- [ ] 키가 없거나 만료된 경우 `(nil)` 반환
- [ ] 값이 존재하면 `"value"` 형태로 반환
- [ ] 반환 성공 시에만 LRU 갱신

#### `DEL key`

- [ ] 삭제 성공 시 `(integer) 1` 반환
- [ ] 키가 없으면 `(integer) 0` 반환
- [ ] 데이터, TTL, LRU 구조에서 엔트리 함께 제거

#### `EXISTS key`

- [ ] 키 존재 여부를 `(integer) 1` 또는 `(integer) 0`으로 반환

#### `DBSIZE`

- [ ] 현재 저장된 키 개수를 `(integer) N`으로 반환

#### `KEYS`

- [ ] 전체 키 목록을 배열 형태로 출력
- [ ] 키 없으면 (empty array) 같은 형태 표현 가능

### 메모리 관리 및 LRU 자동 제거

#### `CONFIG SET maxmemory bytes`

- [ ] 최대 메모리 제한 설정(byte 단위)
- [ ] `bytes`는 0 이상의 정수로 검증
- [ ] `0`은 메모리 무제한으로 처리
- [ ] 성공 시 OK, 정수 파싱 실패 시 에러 표준 출력

#### `INFO memory`

- [ ] 현재 메모리 사용량(`used_memory:<number>`) 출력
- [ ] 최대 메모리 제한(`maxmemory:<number>`) 출력
- [ ] 제거된 키 개수(`evicted_keys:<number>`) 출력

#### 메모리 계산 및 제거 정책

- [ ] `used_memory = sum(len(utf8(key)) + len(utf8(value)))` 기준 적용
- [ ] `maxmemory > 0`이고 SET 이후 메모리 초과 시 LRU 키부터 제거
- [ ] 제거된 키 수를 `evicted_keys`에 누적
- [ ] 단일 엔트리(키 + 값)가 `maxmemory`를 초과하면 저장하지 않고 OOM 에러 반환

### TTL 관리

#### `EXPIRE key seconds`

- [ ] 키의 만료 시간 설정(초 단위)
- [ ] 키가 없으면 `(integer) 0` 반환
- [ ] `seconds <= 0`이면 즉시 만료 처리(존재 시 삭제 후 `(integer) 1` 반환)
- [ ] 정상 설정 시 `(integer) 1` 반환

#### `TTL key`

- [ ] 키의 남은 만료 시간 조회
- [ ] 키가 없으면 `(integer) -2` 반환
- [ ] 키는 존재하지만 만료 시간이 없으면 `(integer) -1` 반환
- [ ] 만료 시간이 있으면 남은 초를 `(integer) N`으로 반환

#### 만료 처리 정책

- [ ] 힙 기반으로 가장 빠른 만료 키 확인
- [ ] lazy deletion 등 만료 힙 정합성 전략 적용 선택
- [ ] 만료된 키는 GET 시 삭제 후 `(nil)` 반환
- [ ] 만료로 삭제된 키는 LRU 갱신하지 않음

### CLI 인터페이스 및 에러 처리

#### CLI REPL

- [ ] `mini-redis>` 프롬프트 출력
- [ ] 사용자 입력 반복 처리
- [ ] 명령어 파싱, 실행, 결과 출력 흐름 구현
- [ ] `exit` 또는 `quit` 입력 시 종료

#### 에러 처리

- [ ] 알 수 없는 명령 에러 처리: `(error) ERR unknown command '<cmd>'`
- [ ] 인자 개수 오류 처리: `(error) ERR wrong number of arguments for '<cmd>' command`
- [ ] 정수 파싱 실패 처리: `(error) ERR value is not an integer or out of range`
- [ ] OOM 에러 처리: `(error) OOM command not allowed when used_memory > 'maxmemory'`

#### 값 파싱

- [ ] 공백 없는 값 입력 지원
- [ ] 큰따옴표로 감싼 값 입력 지원

### 코드 구조

#### 모듈 분리

- [ ] 각 자료구조를 독립 모듈 또는 파일로 분리
- [ ] 핵심 클래스와 함수에 주석 또는 docstring 작성

#### 로직 분리

- [ ] 명령어 파싱 로직과 실행 로직 분리
- [ ] 저장소, LRU, TTL, 메모리 사용량 갱신 흐름을 명확히 분리

### 보너스 과제

#### 동적 배열 직접 구현

##### 기본 연산

- [ ] `append`, `get`, `set`, `remove` 구현

##### 확장 로직

- [ ] capacity 2배 확장 로직 구현
- [ ] 해시맵 버킷 테이블 또는 힙 내부 저장소에 배열 확장 개념 적용

#### 스택/큐/덱 이해와 활용

##### 개념 조사

- [ ] 스택, 큐, 덱 개념 조사

##### 문서화

- [ ] `STACK_QUEUE_DEQUE.md` 문서 작성

#### 이진 트리와 순회 알고리즘

##### 트리 구현

- [ ] 이진 트리 구현

##### 순회 알고리즘

- [ ] 전위, 중위, 후위, 레벨 순회 구현

##### 힙 연계 학습

- [ ] 힙을 완전 이진 트리의 배열 표현 관점에서 설명

#### 이진 탐색 트리(BST)

##### BST 기본 연산

- [ ] 삽입, 탐색, 삭제 구현

##### 정렬 결과

- [ ] 중위 순회 정렬 결과 구현

#### Pub/Sub 기능 구현

##### 명령어

- [ ] `PUBLISH`, `SUBSCRIBE` 명령어 구현

##### 메시징 구조

- [ ] 채널 기반 메시징 구현
- [ ] 연결 리스트를 메시지 큐 또는 구독자별 버퍼로 재활용

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
