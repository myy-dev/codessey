# 사용 예제 (User Demo)

## 값 저장·조회·삭제

자동화 실행:

```bash
python3 scripts/demo_basic_commands.py
```

### SET: 문자열 값 저장

```text
mini-redis> SET greeting "hello world"
OK
```

### GET: 저장된 값 조회

```text
mini-redis> GET greeting
"hello world"
```

### EXISTS: 키 존재 여부 확인

```text
mini-redis> EXISTS greeting
(integer) 1
```

### DBSIZE: 전체 키 개수 조회

```text
mini-redis> DBSIZE
(integer) 1
```

### KEYS: 저장된 키 목록 조회

```text
mini-redis> KEYS
1) "greeting"
```

### DEL: 키 삭제

```text
mini-redis> DEL greeting
(integer) 1
```

### GET: 삭제한 키 조회

```text
mini-redis> GET greeting
(nil)
```

### KEYS: 비어 있는 저장소 조회

```text
mini-redis> KEYS
(empty array)
```

## 메모리 제한 및 LRU 제거 (키와 값의 UTF-8 길이 기준)

자동화 실행:

```bash
python3 scripts/demo_memory_lru.py
```

### CONFIG SET: 최대 메모리 4 bytes 설정

```text
mini-redis> CONFIG SET maxmemory 4
OK
```

### SET: a 저장 (2 bytes)

```text
mini-redis> SET a 1
OK
```

### SET: b 저장 (누적 4 bytes)

```text
mini-redis> SET b 2
OK
```

### GET: a 조회로 최근 사용 갱신

```text
mini-redis> GET a
"1"
```

### CONFIG SET: 한도 축소 및 최근 사용 이력이 낮은 b 제거

```text
mini-redis> CONFIG SET maxmemory 2
OK
```

### INFO memory: 사용량 및 제거 횟수 조회

```text
mini-redis> INFO memory
used_memory:2
maxmemory:2
evicted_keys:1
```

### SET: 최대 메모리 초과 입력

```text
mini-redis> SET huge abcde
(error) OOM command not allowed when used_memory > 'maxmemory'
```

### CONFIG SET: 최대 메모리 제한 해제

```text
mini-redis> CONFIG SET maxmemory 0
OK
```

## TTL 설정·초기화·즉시 만료

### SET: TTL 대상 값 저장

```text
mini-redis> SET session active
OK
```

### TTL: 만료 시간이 없는 키 조회

```text
mini-redis> TTL session
(integer) -1
```

### EXPIRE: 60초 만료 시간 설정

```text
mini-redis> EXPIRE session 60
(integer) 1
```

### TTL: 남은 초 조회 (입력 사이 경과 시간에 따라 변동)

```text
mini-redis> TTL session
(integer) N
```

### SET: 기존 값 덮어쓰기 및 TTL 초기화

```text
mini-redis> SET session refreshed
OK
```

### TTL: 초기화된 만료 시간 조회

```text
mini-redis> TTL session
(integer) -1
```

### EXPIRE: 3초 만료 시간 설정

```text
mini-redis> EXPIRE session 3
(integer) 1
```

### GET: 3초 경과 후 만료된 키 조회

```text
mini-redis> GET session
(nil)
```

### TTL: 만료된 키 조회

```text
mini-redis> TTL session
(integer) -2
```

## Pub/Sub 채널 구독 및 메시지 발행

### SUBSCRIBE: news 채널 구독

```text
mini-redis> SUBSCRIBE news
1) "subscribe"
2) "news"
3) (integer) 1
```

### PUBLISH: news 채널에 메시지 발행

```text
mini-redis> PUBLISH news "hello world"
(integer) 1
```

## 잘못된 명령 및 인자

### 알 수 없는 명령 입력

```text
mini-redis> UNKNOWN
(error) ERR unknown command 'UNKNOWN'
```

### GET: 인자 누락

```text
mini-redis> GET
(error) ERR wrong number of arguments for 'get' command
```

### EXPIRE: 정수가 아닌 만료 시간

```text
mini-redis> EXPIRE missing abc
(error) ERR value is not an integer or out of range
```
