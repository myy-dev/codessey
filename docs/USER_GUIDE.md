# 사용자 가이드 (User Guide)

실행 위치: 프로젝트 루트

CLI 실행 명령: `python3 main.py` 또는 `python3 -m mini_redis`

종료 명령: `exit`, `quit`

- [사용 예제](USER_DEMO.md)

## 실행 및 테스트 (Run & Test)

실행 위치: 프로젝트 루트

```bash
# CLI 실행
python3 main.py

# 패키지 모듈로 실행
python3 -m mini_redis

# 전체 단위 테스트 실행
python3 -m unittest discover -v
```

종료 방법: CLI에서 `exit` 또는 `quit` 입력

## 명령어 명세 (Command Specification)

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

## 단일 프로세스 Pub/Sub 사용

통신 범위: 단일 프로세스

공유 객체: 여러 저장소 인스턴스 간 동일 `PubSubManager`

메시지 발행: `PUBLISH` 호출 시 구독자별 연결 리스트 버퍼에 메시지 저장

메시지 조회: `read_messages` 호출 시 발행 순서대로 메시지 반환 및 버퍼 비우기

```python
from mini_redis.pubsub import PubSubManager
from mini_redis.store import MiniRedisStore

bus = PubSubManager()
subscriber = MiniRedisStore(pubsub_manager=bus, subscriber_id="client-1")
publisher = MiniRedisStore(pubsub_manager=bus)

subscriber.execute(["SUBSCRIBE", "news"])
publisher.execute(["PUBLISH", "news", "hello"])
assert subscriber.read_messages("news") == ["hello"]
```

메모리 및 LRU 집계 제외 대상: 키-값 데이터가 아닌 Pub/Sub 버퍼
