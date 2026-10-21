# 컴퓨터가 갑자기 느려지거나 멈췄을 때 원인 찾아 고치기

## 프로젝트 개요 (Project Overview)

과제 제공 앱의 메모리 증가·CPU 과점유·교착상태 재현 및 관제·로그 기반 원인 분석과 조치 전후 비교 프로젝트

## 실행 환경 (Environment)

- **운영체제·아키텍처**: Ubuntu 24.04 LTS / ARM64
- **컨테이너 조건**: 외부 네트워크 차단, 메모리 768MB, CPU 1개 분량, PID 64개
- **제공 앱**: `agent-app-leak/agent-leak-app-arm64`
- **실행 계정**: `appuser`
- **사용 도구**: Shell, `monitor.sh`, `/proc`, `ps`, `ps -L`, `pgrep`, `kill`

## 프로젝트 구조 (Project Structure)

```text
.
├── README.md                     # 프로젝트 설명 및 수행 항목 체크리스트
├── Dockerfile                    # 일반 사용자 실행 환경·디렉터리·키 준비
├── compose.yaml                  # 컨테이너 격리·자원 제한·장애 설정
├── agent-app-leak/
│   └── agent-leak-app-arm64      # ARM64 제공 원본
├── scripts/
│   └── monitor.sh               # 실제 워커의 CPU·RSS·상태·스레드 관제
├── docs/
│   ├── USER_DEMO.md             # 동료 평가용 실행·관제·종료 명령
│   ├── EVIDENCE.md              # 실행 환경·증거 목록·관제 수치 해석
│   └── reports/
│       ├── oom-report.md        # 메모리 증가·MemoryGuard 종료 분석
│       ├── cpu-report.md        # CPU 부하 증가·보호 종료 분석
│       └── deadlock-report.md   # 순환 자원 대기·작업 중단 분석
└── evidence/
    ├── revalidation.log        # 별도 재실행의 종료 코드·경과시간·정리 기록
    └── generated/              # 앱·관제 로그 및 프로세스·스레드 출력 원문
```

### 프로젝트 흐름

```text
Docker 실습 환경 준비
        ↓
장애 조건으로 제공 앱 실행
        ↓
실제 워커의 관제·로그·스레드 증거 수집
        ↓
환경변수 변경 후 재실행 및 조치 전후 비교
        ↓
GitHub Issue 형식의 분석 리포트 3건 작성
```

## 수행 항목 체크리스트

### 사전 준비 및 앱 부트 조건

- [x] 제공 ARM64 원본 실행 파일을 압축 해제해 프로젝트에 보관
- [x] 컨테이너 아키텍처를 `linux/arm64`로 명시하고 원본 직접 실행
- [x] root가 아닌 `appuser` 계정으로 앱 실행
- [x] `AGENT_HOME` 설정 및 디렉터리 생성
- [x] `AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files` 설정 및 디렉터리 생성
- [x] `AGENT_KEY_PATH=$AGENT_HOME/api_keys` 설정 및 디렉터리 생성
- [x] `AGENT_LOG_DIR` 설정 및 일반 계정의 로그 쓰기 권한 확보
- [x] `$AGENT_HOME/api_keys/secret.key` 생성 및 `agent_api_key_test` 저장
- [x] `AGENT_PORT=15034` 설정 및 포트 사용 가능 부트 조건 통과
- [x] `MEMORY_LIMIT`·`CPU_MAX_OCCUPY`·`MULTI_THREAD_ENABLE` 실험 조건 설정
- [x] 제공 앱의 Boot Sequence 6단계 통과 및 `Agent READY` 확인

### 프로세스 관제 및 증거 수집

- [x] 원본 실행기의 부모 PID와 실제 워커 PID 구분
- [x] `monitor.sh`로 실제 워커의 CPU·RSS·프로세스 상태·스레드 수 수집
- [x] `/proc`의 CPU 시간 증가량과 경과 시간을 이용한 구간 CPU 사용률 계산
- [x] 앱 실행 로그와 워커 관제 로그를 실험별 파일로 분리
- [x] 앱 내부 Heap·부하 값과 OS 관측 RSS·CPU 수치 구분
- [x] 앱 자체의 보호 종료와 관측 후 외부 정리 구분

### 메모리 증가 및 OOM 분석

- [x] `monitor.sh`로 실제 워커 RSS의 `10.1→41.6MB` 상승 관측
- [x] `Current Heap`의 `25→50MB` 증가 및 `Memory limit exceeded` 로그 수집
- [x] MemoryGuard의 자기 종료 로그와 `SIGKILL` 종료 확인
- [x] 메모리 누적과 앱 내부 보호 정책에 따른 종료 원인 추론
- [x] `MEMORY_LIMIT=50→512` 변경 전후 실행 비교
- [x] 약 5초 후 보호 종료와 12초 관측 중 생존 결과 기록
- [x] [메모리/OOM 분석 리포트](docs/reports/oom-report.md) 작성

### CPU 과점유 분석

- [x] 시스템 전체가 아닌 실제 워커의 CPU 사용률 상승 관측
- [x] 앱 부하 증가와 `CPU Threshold Violated!` 로그 수집
- [x] CPU 보호 동작에 따른 `SIGTERM` 종료 원인 추론
- [x] `CPU_MAX_OCCUPY=100→20` 변경 전후 실행 비교
- [x] 관제 최고 CPU `45.5→18.2%` 및 약 30초 후 보호 종료·40초 관측 중 생존 결과 기록
- [x] [CPU 과점유 분석 리포트](docs/reports/cpu-report.md) 작성

### 교착상태(Deadlock) 진단

- [x] `ps -ef`로 작업 중단 상태의 PID 유지 확인
- [x] `ps -L`로 메인·워커 스레드의 `futex_wait_queue` 대기 확인
- [x] 교착 후 CPU `0.0%`·RSS `16.7MB`·스레드 3개 정체 관측
- [x] 마지막 `WAITING`·`BLOCKED` 로그 및 이후 로그 무진행 확인
- [x] 두 워커의 상반된 자원 획득 순서와 순환 대기 추론
- [x] 상호 배제·점유 대기·비선점·순환 대기의 네 조건 분석
- [x] `MULTI_THREAD_ENABLE=true→false` 변경 전후 실행 비교
- [x] 14초 관측 중 작업 중단과 설정 변경 후 작업 진행 결과 기록
- [x] [교착상태 분석 리포트](docs/reports/deadlock-report.md) 작성

### 분석 리포트 및 제출 증거

- [x] OOM·CPU·Deadlock의 GitHub Issue 형식 리포트 3건 작성
- [x] 각 리포트에 발생 현상·재현 조건·증거·원인 분석·조치 및 검증 포함
- [x] 로그와 OS 관측에 근거한 원인 추론 및 관련 OS 동작 원리 설명
- [x] 환경변수 변경 전후의 수치·생존 여부·작업 진행 비교
- [x] 앱·관제 로그와 `ps` 출력 원문 총 13개 보관
- [x] 별도 재실행의 종료 코드·경과시간·외부 정리 기록 보관
- [x] 원본 디컴파일 없이 관측된 사실과 추론 범위 구분

## 결과물 (Deliverables)

| 문서 | 내용 |
| --- | --- |
| [메모리/OOM 분석 리포트](docs/reports/oom-report.md) | 메모리 증가·보호 종료·설정 변경 검증 |
| [CPU 과점유 분석 리포트](docs/reports/cpu-report.md) | CPU 상승·보호 종료·설정 변경 검증 |
| [교착상태 분석 리포트](docs/reports/deadlock-report.md) | 순환 대기 분석·멀티스레드 설정 변경 검증 |
| [실행 증거 및 관제 해석](docs/EVIDENCE.md) | 원문 증거·실행 환경·관측 한계 |
| [평가 시연 가이드](docs/USER_DEMO.md) | 실행·관제·결과 확인·로그 보관·종료 명령 |
