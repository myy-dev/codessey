# Python과 Git 심화, 나만의 용돈 기입장 프로그램 만들기

## 프로젝트 개요 (Project Overview)

- Python 표준 라이브러리만으로 구현하는 파일 기반 콘솔 가계부 프로그램입니다.
- 수입과 지출의 추가·조회·수정·삭제뿐 아니라 검색, 월별 요약, 예산 관리, 카테고리 관리, CSV 가져오기·내보내기를 지원합니다.
- 제너레이터 스트리밍, 데코레이터, 타입 힌트, 계층별 모듈 분리를 적용해 데이터가 많아져도 유지보수하기 쉬운 작은 서비스를 만드는 것이 목표입니다.

| 분야 | 구분 | 학습 시간 |
| --- | --- | --- |
| AI/SW 기초 | Python과 Git 심화 | 60시간 |

## 실행 환경 (Environment)

- **언어**: Python 3.10 이상
- **인터페이스**: 터미널 기반 CLI
- **저장 형식**: JSONL
- **외부 라이브러리**: 사용하지 않음 (Python 표준 라이브러리만 사용)

## 프로젝트 구조 (Project Structure)

아래는 현재 구현된 프로젝트 구조입니다.

```text
.
├── budget_app/
│   ├── __init__.py         # 패키지 초기화
│   ├── __main__.py         # `python -m budget_app` 실행 진입점
│   ├── cli.py              # 명령어와 옵션 파싱, 대화형 입력
│   ├── models.py           # Transaction 등 데이터 모델
│   ├── repositories.py     # JSONL 파일 읽기·쓰기 및 스트리밍
│   ├── services.py         # 거래, 예산, 요약 등 비즈니스 로직
│   ├── validators.py       # 날짜, 금액, 타입, 카테고리 검증
│   ├── decorators.py       # 예외 처리, 실행 로그, 시간 측정
│   ├── errors.py           # 사용자용 오류와 해결 힌트
│   └── formatters.py       # 콘솔 출력 형식
├── data/
│   ├── transactions.jsonl  # 거래 내역
│   ├── categories.jsonl    # 카테고리 목록
│   ├── budgets.jsonl       # 월별 예산
│   ├── recurring.jsonl     # 반복 거래 규칙
│   └── sequences.jsonl     # 삭제 후에도 재사용되지 않는 ID 시퀀스
├── tests/
│   ├── test_cli.py         # CLI와 종료 코드 테스트
│   ├── test_services.py    # 서비스·저장소 통합 테스트
│   └── test_validators.py  # 입력 검증 테스트
├── .gitignore
└── README.md               # 프로젝트 문서
```

## 실행 방법 (Getting Started)

```bash
# 전체 도움말
python -m budget_app --help

# 명령별 도움말
python -m budget_app add --help

# 저장 폴더를 직접 지정하는 경우
python -m budget_app --data-dir ./data list --limit 10
```

- 기본 저장 폴더는 `./data`입니다.
- 저장 파일이 없으면 프로그램이 폴더와 파일을 자동 생성합니다.
- 카테고리 파일이 비어 있으면 `food`, `transport`, `rent`, `salary`, `etc` 기본 카테고리를 생성합니다.
- 모든 명령은 `--help` 옵션을 지원하며, 정상 종료 시 종료 코드 `0`, 오류 발생 시 `0`이 아닌 종료 코드를 반환합니다.

## 수행 항목 체크리스트

### 데이터 모델 및 프로그램 구조

- [x] `Transaction`을 `dataclass`로 정의
- [x] 거래 필드 `id`, `type`, `date`, `amount`, `category`, `memo`, `tags` 구성
- [x] 최소 2개 이상의 클래스 사용
- [x] CLI, 모델, 저장소, 서비스 등 최소 3개 이상의 모듈로 책임 분리
- [x] 모든 함수와 주요 데이터 구조에 타입 힌트 적용
- [x] 스택트레이스 대신 오류 원인과 해결 힌트 출력
- [x] 정상 종료 코드 `0`, 오류 종료 코드 `0` 이외의 값 적용

### 거래 관리 (CRUD)

- [x] `add` 명령으로 대화형 거래 추가
- [x] 저장 완료 후 유일한 거래 ID 출력
- [x] `list --limit N` 명령으로 최신순 거래 조회 (`--limit` 기본값: `20`)
- [x] `update --id <id>`와 `--date`, `--type`, `--category`, `--amount`, `--memo`, `--tags` 옵션으로 거래 수정
- [x] `delete --id <id>` 명령으로 거래 삭제
- [x] 수정·삭제 대상 ID가 없을 때 안내 메시지 출력
- [x] 수정·삭제 시 데이터 손실을 방지하는 안전한 파일 재작성 적용

### 입력값 검증

- [x] 날짜가 `YYYY-MM-DD` 형식인지 검증
- [x] 금액이 `0`보다 큰 정수인지 검증
- [x] 거래 타입이 `income` 또는 `expense`인지 검증
- [x] 등록된 카테고리만 거래에 사용할 수 있도록 검증
- [x] 잘못된 대화형 입력에 재입력 요청 또는 해결 가능한 오류 메시지 제공

### 검색 및 요약

- [x] `search`에서 `--from`, `--to` 기간 조건 지원
- [x] `search`에서 `--category`, `--type`, `--q`, `--tag` 조건 지원
- [x] 검색 결과를 최신순으로 출력
- [x] `summary --month YYYY-MM`으로 월별 총수입·총지출·잔액 출력
- [x] `summary --top N`으로 카테고리별 지출 상위 N개 출력
- [x] 거래가 없는 달에 데이터 없음 메시지 출력

### 예산 및 카테고리 관리

- [x] `budget set --month YYYY-MM --amount <금액>`으로 월 예산 저장
- [x] 월별 요약에 예산 사용률 표시
- [x] 예산 초과 시 경고 메시지 출력
- [x] `category add/list/remove` 명령 구현
- [x] 사용 중인 카테고리는 삭제되지 않도록 차단하고 이유 안내

### 파일 저장 및 스트리밍

- [x] 거래·카테고리·예산을 3개 이상의 파일로 분리해 영구 저장
- [x] `--data-dir` 옵션으로 저장 폴더 변경 지원
- [x] 저장 파일과 폴더가 없을 때 자동 생성
- [x] 거래 목록과 검색에서 파일 전체를 한 번에 읽지 않고 `yield` 기반 제너레이터 사용
- [x] 예외 처리, 실행 로그 또는 실행 시간 측정 데코레이터를 1개 이상 구현하고 적용

### CSV 가져오기 및 내보내기

- [x] `import --from <csv>`로 거래 일괄 등록
- [x] `export --out <csv> --month YYYY-MM`으로 월별 거래 내보내기
- [x] `export --out <csv> --from YYYY-MM-DD --to YYYY-MM-DD`로 기간별 거래 내보내기
- [x] 내보내기 시 `--month` 또는 `--from`·`--to` 조건 중 하나를 필수로 입력
- [x] 가져오기·내보내기 완료 후 처리 건수 출력
- [x] UTF-8 인코딩, 헤더 포함, 고정 CSV 스키마 적용

## 주요 명령 (Command Reference)

| 명령 | 설명 | 주요 옵션 및 입력 |
| --- | --- | --- |
| `add` | 거래를 대화형으로 추가 | 날짜, 타입, 카테고리, 금액, 메모, 태그 |
| `list` | 거래를 날짜 최신순으로 조회 | `--limit N` (기본값: `20`) |
| `search` | 조건에 맞는 거래 검색 | `--from`, `--to`, `--category`, `--type`, `--q`, `--tag` |
| `summary` | 월별 수입·지출·잔액과 지출 순위 조회 | `--month YYYY-MM`, `--top N` |
| `budget set` | 월 예산 설정 | `--month YYYY-MM`, `--amount <금액>` |
| `budget get` | 월 예산 조회 | `--month YYYY-MM` |
| `category add` | 카테고리 추가 | 대화형 입력 또는 `--name` |
| `category list` | 카테고리 목록 조회 | 없음 |
| `category remove` | 카테고리 삭제 | 대화형 입력 또는 `--name` |
| `update` | ID 기준으로 거래 수정 | `--id`, `--date`, `--type`, `--category`, `--amount`, `--memo`, `--tags` |
| `delete` | ID 기준으로 거래 삭제 | `--id <id>` |
| `import` | CSV 파일에서 거래 가져오기 | `--from <csv>` |
| `export` | 조건에 맞는 거래를 CSV로 내보내기 | `--out <csv>`와 `--month` 또는 `--from`·`--to` 중 하나 필수 |
| `backup` | 데이터 파일을 ZIP으로 백업 | `--out-dir <폴더>` |
| `recurring add` | 반복 거래 규칙 추가 | `--type`, `--category`, `--amount`, `--day`, `--memo`, `--tags` |
| `recurring list` | 반복 거래 규칙 조회 | 없음 |
| `recurring remove` | 반복 거래 규칙 삭제 | `--id <id>` |
| `recurring generate` | 특정 월의 반복 거래 생성 | `--month YYYY-MM` |

### 명령 사용 예시

```bash
# 거래 추가
python -m budget_app add

# 최근 거래 10건 조회
python -m budget_app list --limit 10

# 2024년 1월 식비 지출 검색
python -m budget_app search \
  --from 2024-01-01 \
  --to 2024-01-31 \
  --category food \
  --type expense

# 2024년 1월 요약과 지출 상위 3개 카테고리 조회
python -m budget_app summary --month 2024-01 --top 3

# 월 예산 설정
python -m budget_app budget set --month 2024-01 --amount 500000

# 거래 수정 (옵션 기반 방식으로 고정)
python -m budget_app update --id TX-000012 --amount 18000 --memo "저녁"

# 거래 삭제
python -m budget_app delete --id TX-000012

# CSV 가져오기
python -m budget_app import --from import.csv

# 월별 CSV 내보내기
python -m budget_app export --out export.csv --month 2024-01

# 반복 거래 등록 및 2024년 2월 거래 생성
python -m budget_app recurring add \
  --type expense \
  --category rent \
  --amount 500000 \
  --day 31 \
  --memo "월세"
python -m budget_app recurring generate --month 2024-02

# 전체 데이터 백업
python -m budget_app backup --out-dir ./backups

# 자동 테스트 실행
python -m unittest discover -v
```

## 저장 파일 위치 및 형식 (Data Storage)

기본적으로 `./data` 아래의 JSONL 파일 5개에 데이터를 저장합니다. JSONL은 한 줄에 하나의 JSON 객체를 기록하는 형식입니다.

| 파일 | 저장 내용 | 주요 필드 |
| --- | --- | --- |
| `data/transactions.jsonl` | 거래 내역 | `id`, `type`, `date`, `amount`, `category`, `memo`, `tags` |
| `data/categories.jsonl` | 사용 가능한 카테고리 | `name` |
| `data/budgets.jsonl` | 월별 예산 | `month`, `amount` |
| `data/recurring.jsonl` | 반복 거래 규칙 | `id`, `type`, `category`, `amount`, `day`, `memo`, `tags` |
| `data/sequences.jsonl` | 영구 ID 시퀀스 | `name`, `value` |

- 거래 파일은 날짜와 ID 오름차순으로 저장되며, 목록과 검색에서는 역방향으로 읽어 날짜 최신순을 보장합니다.
- ID 시퀀스를 별도 저장하므로 거래나 반복 규칙을 삭제해도 기존 ID를 다시 사용하지 않습니다.

거래 저장 예시:

```json
{"id":"TX-000012","type":"expense","date":"2024-01-15","amount":15000,"category":"food","memo":"점심","tags":["meal"]}
```

## Import/Export CSV 스키마

- 문자 인코딩: UTF-8
- 첫 번째 행: 헤더 필수
- `tags`: 태그가 여러 개인 경우 쉼표(`,`)로 구분
- 가져오기는 모든 행을 먼저 검증하고, 유효한 행을 원자적으로 일괄 반영하며 잘못된 행은 처리 건수에 포함해 건너뜁니다.
- 내보내기는 데이터 저장 파일과의 경로 충돌을 차단하고, 임시 파일 작성이 끝난 뒤 결과 CSV를 원자적으로 교체합니다.

| column | required | 형식 및 설명 |
| --- | --- | --- |
| `date` | Y | `YYYY-MM-DD` |
| `type` | Y | `income` 또는 `expense` |
| `category` | Y | 등록된 카테고리 |
| `amount` | Y | `0`보다 큰 정수 |
| `memo` | N | 문자열 |
| `tags` | N | 쉼표로 구분한 문자열 |

```csv
date,type,category,amount,memo,tags
2024-01-15,expense,food,15000,점심,meal
2024-01-25,income,salary,3000000,월급,"salary,monthly"
```

## 보너스 과제

- [x] **백업 기능**: `backup` 실행 시 타임스탬프가 포함된 ZIP 백업 파일 생성
- [x] **반복 내역 기능**: 월급·월세 등 반복 규칙을 등록하고 특정 월의 거래 자동 생성
- [x] **테이블 정렬 출력**: 외부 라이브러리 없이 문자열 정렬로 콘솔 가독성 개선
- [x] **저장 원자성 강화**: 수정·삭제 시 임시 파일 작성 후 `os.replace`로 교체

## 제약 사항 (Constraints)

- **Python 버전**: Python 3.10 이상
- **외부 라이브러리 사용 금지**: 별도의 `pip install` 없이 표준 라이브러리만 사용
- **저장 방식**: JSONL 또는 CSV 중 한 가지 형식 사용
- **저장 파일 분리**: 거래·카테고리·예산을 포함한 3개 이상의 파일 사용
- **CLI 옵션 표기**: `--help`, `--limit`, `--from`처럼 이중 하이픈(`--`) 사용
- **메모리 사용**: 목록과 검색은 제너레이터로 스트리밍 처리
- **오류 처리**: 사용자에게 스택트레이스를 노출하지 않고 원인과 해결 힌트 제공
- **수정 방식**: `update --id <id> [변경 옵션]` 형태의 옵션 기반 방식으로 고정
- **카테고리 삭제 정책**: 거래에서 사용 중인 카테고리는 삭제 차단

## 결과물 (Deliverables)

- [x] 실행 가능한 콘솔 가계부 애플리케이션
- [x] 거래·카테고리·예산·반복 규칙·ID 시퀀스 데이터 파일 5개
- [x] 표준 라이브러리 `unittest` 기반 자동 테스트
- [x] 실행 방법, 저장 형식, 명령 예시, CSV 스키마를 포함한 `README.md`
