# 사용자 가이드 (User Guide)

## 실행 및 테스트 (Run & Test)

```bash
# CLI 실행
python3 main.py

# CLI 종료 입력: exit 또는 quit
```

## 명령어 명세 (Command Specification)

| 명령어                       | 설명                  | 성공 출력                                     |
| ---------------------------- | --------------------- | --------------------------------------------- |
| `SET <key> <value>`          | 키에 값 저장          | `OK`                                          |
| `GET <key>`                  | 키의 값 조회          | `"value"` 또는 `(nil)`                        |
| `DEL <key>`                  | 키 삭제               | `(integer) 1` 또는 `(integer) 0`              |
| `EXISTS <key>`               | 키 존재 여부 확인     | `(integer) 1` 또는 `(integer) 0`              |
| `DBSIZE`                     | 전체 키 개수 조회     | `(integer) N`                                 |
| `KEYS`                       | 전체 키 목록 출력     | 배열 형태                                     |
| `CONFIG SET maxmemory <bytes>` | 최대 메모리 제한 설정 | `OK`                                        |
| `INFO memory`                | 메모리 정보 조회      | `used_memory`, `maxmemory`, `evicted_keys`    |
| `EXPIRE <key> <seconds>`     | TTL 설정              | `(integer) 1` 또는 `(integer) 0`              |
| `TTL <key>`                  | 남은 TTL 조회         | `(integer) N`, `(integer) -1`, `(integer) -2` |
| `SUBSCRIBE <channel>`        | 채널 구독             | 구독 확인 배열                                |
| `PUBLISH <channel> <message>` | 메시지 발행          | 메시지를 받은 구독자 수                       |

- 메모리 제한: `CONFIG SET maxmemory 0` 설정 시 제한 해제
- TTL 반환값: `-2` 키 없음 또는 만료, `-1` 만료 시간 미설정, `0` 이상 남은 만료 시간(초)

### Pub/Sub 응답

#### SUBSCRIBE

```text
mini-redis> SUBSCRIBE news
1) "subscribe"
2) "news"
3) (integer) 1
```

| 항목 | 의미 |
| --- | --- |
| `1) "subscribe"` | 구독 등록 확인 |
| `2) "news"` | 구독한 채널 이름 |
| `3) (integer) 1` | 현재 구독자가 구독 중인 전체 채널 수 |

#### PUBLISH

```text
mini-redis> PUBLISH news "hello"
(integer) 1
```

| 응답 | 의미 |
| --- | --- |
| `(integer) N` | 메시지를 받은 구독자 수 |
