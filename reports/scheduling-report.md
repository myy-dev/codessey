# [Analysis] 작업 단위 Round-Robin 시뮬레이션의 로그 패턴 분석

## 1. 로그 관찰 개요

정상 실행 모드의 `run_normal_scenario()`는 단일 스레드 반복문에서 작업 A·B·C의 진행 값을 25%씩 증가시키고 순환 로그를 출력합니다. 로그의 `Thread-A`, `Thread-B`, `Thread-C`는 작업을 나타내는 이름이며 실제 생성된 스레드가 아닙니다. 각 작업의 진행 값이 100%에 도달하기 전에 다음 작업의 진행 값을 갱신하는 작업 단위 Round-Robin 시뮬레이션입니다.

## 2. 증거 자료

![Round-Robin 실행 순서](../evidence/charts/scheduling-timeline.svg)

```text
[Thread-A] Task Started. Calculating... (25%)
[Thread-B] Task Started. Calculating... (25%)
[Thread-C] Task Started. Calculating... (25%)
[Thread-A] Resumed. Calculating... (50%)
[Thread-B] Resumed. Calculating... (50%)
[Thread-C] Resumed. Calculating... (50%)
```

- [전체 스케줄링 로그](../evidence/generated/scheduling-round-robin.log)
- [스케줄링 관제 로그](../evidence/generated/scheduling-round-robin-monitor.log)

## 3. 패턴 분석 및 결론

- **순환 순서**: 작업 진행 로그가 A→B→C 순서로 네 차례 반복됩니다.
- **동일 진행 단위**: 각 작업의 진행 값은 선택될 때마다 25%씩 증가합니다.
- **구현과 로그 일치**: 단일 스레드 반복문에서 A·B·C를 차례로 선택하는 구현이 `policy=round-robin` 진단 로그 및 출력 순서와 일치합니다.

확인된 범위는 애플리케이션의 **작업 단위 Round-Robin 순환 시뮬레이션**입니다. `quantum=0.03s`는 각 로그 출력 후 호출하는 `time.sleep()`의 설정값입니다. 이 구현과 로그는 실제 워커 스레드의 선점, 커널의 시간 할당량 또는 OS 스케줄러 정책을 검증하지 않으며, FCFS·Priority 등 OS 스케줄링 알고리즘을 배제하는 근거로 사용할 수 없습니다.

## 4. 장단점 및 적합한 아키텍처

다음은 일반적인 Round-Robin 알고리즘의 장단점과 적용 사례입니다. 이번 시뮬레이션에서 문맥 교환 비용, 응답 지연 또는 처리량을 측정한 결과는 아닙니다.

| 구분 | 분석 |
| --- | --- |
| 장점 | 작업마다 공평한 실행 기회를 제공하고 긴 작업 하나가 전체를 독점하는 것을 막습니다. |
| 단점 | 시간 할당량이 너무 짧으면 문맥 교환 비용이 커지고, 너무 길면 응답성이 떨어집니다. |
| 적합 | 여러 요청에 빠르게 응답해야 하는 대화형 웹 서버, 시분할 시스템 |
| 덜 적합 | 작업 전환 비용이 크고 총 처리량이 더 중요한 순차 배치 처리 |
