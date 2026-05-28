# 6단계 구현 후 면접/학습 개념 정리

6단계는 maxmemory와 LRU eviction을 구현하는 단계이다. 핵심은 제한된 메모리 안에서 어떤 키를 제거할지 결정하고, 제거 과정에서도 저장소 상태를 일관되게 유지하는 것이다.

## 1. 핵심 개념

- `maxmemory`는 저장 가능한 메모리 상한이다.
- `used_memory`는 key와 value의 UTF-8 바이트 길이 합으로 계산한다.
- LRU는 Least Recently Used, 가장 오래 사용되지 않은 데이터를 먼저 제거하는 정책이다.
- `evicted_keys`는 LRU 정책으로 제거된 키 수를 누적한다.

## 2. 메모리 계산

이 프로젝트의 메모리 계산은 단순화되어 있다.

```text
used_memory = sum(len(key.encode("utf-8")) + len(value.encode("utf-8")))
```

자료구조 오버헤드는 계산하지 않는다.

## 3. LRU eviction 흐름

1. `SET`으로 값을 저장한다.
2. `used_memory`를 갱신한다.
3. `maxmemory > 0`이고 사용량이 초과되었는지 확인한다.
4. 초과했다면 LRU tail부터 제거한다.
5. 제거된 키는 데이터, TTL, LRU, 메모리 상태에서 모두 삭제한다.
6. `evicted_keys`를 증가시킨다.

## 4. OOM 처리

단일 엔트리의 key+value 크기가 `maxmemory`보다 크면 LRU로 다른 키를 제거해도 저장할 수 없다. 이 경우 저장하지 않고 OOM 에러를 반환한다.

## 5. 구현 후 설명할 수 있어야 하는 것

- LRU가 어떤 기준으로 데이터를 제거하는가?
- LRU 구현에 해시맵과 이중 연결 리스트가 함께 필요한 이유는 무엇인가?
- maxmemory 초과 시 eviction과 OOM의 차이는 무엇인가?
- UTF-8 바이트 길이로 메모리를 계산하는 이유는 무엇인가?
- maxmemory를 줄였을 때 기존 데이터는 어떻게 처리해야 하는가?

## 6. 면접 질문 예시

- LRU Cache를 설계해보세요.
- Cache eviction policy에는 어떤 것들이 있나요?
- LRU와 LFU의 차이는 무엇인가요?
- 메모리 제한이 있는 key-value store에서 쓰기 요청은 어떤 순서로 처리하나요?

## 7. 자가 점검

- [ ] `GET` 성공과 `SET` 성공 시 LRU가 갱신되는가?
- [ ] eviction 시 tail부터 제거되는가?
- [ ] OOM 상황에서 기존 데이터가 잘못 변경되지 않는가?
- [ ] `INFO memory` 값이 실제 상태와 일치하는가?
