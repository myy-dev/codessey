# 사용 예제 (User Demo)

실행 위치: 프로젝트 루트

CLI 실행 명령:

```bash
python3 -m mini_redis
```

각 CLI 예제의 기준: 새 세션

입력 프롬프트: `mini-redis>`

종료 명령: `exit`, `quit`

## 값 저장·조회·삭제

```text
mini-redis> SET greeting "hello world"
OK
mini-redis> GET greeting
"hello world"
mini-redis> EXISTS greeting
(integer) 1
mini-redis> DBSIZE
(integer) 1
mini-redis> KEYS
1) "greeting"
mini-redis> DEL greeting
(integer) 1
mini-redis> GET greeting
(nil)
mini-redis> KEYS
(empty array)
```

## TTL 설정·초기화·즉시 만료

```text
mini-redis> SET session active
OK
mini-redis> TTL session
(integer) -1
mini-redis> EXPIRE session 60
(integer) 1
mini-redis> SET session refreshed
OK
mini-redis> TTL session
(integer) -1
mini-redis> EXPIRE session 0
(integer) 1
mini-redis> GET session
(nil)
mini-redis> TTL session
(integer) -2
```

`SET`으로 기존 값을 덮어쓸 때 TTL 초기화

양수 TTL 조회 결과: 입력 사이 경과 시간에 따라 달라지는 남은 초

`EXPIRE`에 0 이하 지정 시 즉시 삭제

## 메모리 제한과 LRU 제거

각 엔트리(`a=1`, `b=2`, `c=3`)의 크기: 키와 값의 UTF-8 길이 합계인 2 bytes

`a` 조회 후 `c` 저장 시 제거 대상: 가장 오래 사용하지 않은 `b`

```text
mini-redis> CONFIG SET maxmemory 4
OK
mini-redis> SET a 1
OK
mini-redis> SET b 2
OK
mini-redis> GET a
"1"
mini-redis> SET c 3
OK
mini-redis> GET b
(nil)
mini-redis> INFO memory
used_memory:4
maxmemory:4
evicted_keys:1
mini-redis> SET huge abcde
(error) OOM command not allowed when used_memory > 'maxmemory'
```

`CONFIG SET maxmemory 0`: 메모리 제한 해제

## 잘못된 명령 및 인자

```text
mini-redis> UNKNOWN
(error) ERR unknown command 'UNKNOWN'
mini-redis> GET
(error) ERR wrong number of arguments for 'get' command
mini-redis> EXPIRE missing abc
(error) ERR value is not an integer or out of range
```

## 단일 프로세스 Pub/Sub

여러 저장소의 동일 `PubSubManager` 공유 예제

실행 위치: 프로젝트 루트의 Python 실행 환경

```python
from mini_redis.pubsub import PubSubManager
from mini_redis.store import MiniRedisStore

bus = PubSubManager()
subscriber = MiniRedisStore(pubsub_manager=bus, subscriber_id="client-1")
publisher = MiniRedisStore(pubsub_manager=bus)

print(subscriber.execute(["SUBSCRIBE", "news"]))
print(publisher.execute(["PUBLISH", "news", "hello"]))
print(publisher.execute(["PUBLISH", "news", "world"]))
print(subscriber.read_messages("news"))
print(subscriber.read_messages("news"))
```

예상 출력:

```text
1) "subscribe"
2) "news"
3) (integer) 1
(integer) 1
(integer) 1
['hello', 'world']
[]
```

`read_messages`: 발행 순서에 따른 메시지 반환 및 버퍼 비우기

별도 CLI 프로세스 간 구독 공유 불가

CLI 메시지 버퍼 조회 명령 미제공
