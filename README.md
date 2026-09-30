# Python과 Git 심화, 나만의 용돈 기입장 프로그램 만들기

## 프로젝트 개요 (Project Overview)

Python 표준 라이브러리만으로 구현하는 파일 기반 콘솔 가계부 프로그램

## 프로젝트 구조 (Project Structure)

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
│   ├── decorators.py       # CLI 예외 처리 데코레이터
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
├── docs/
│   ├── USER_GUIDE.md       # 실행 방법과 명령어 안내
│   ├── USER_DEMO.md        # 기능 시연 순서와 명령어
│   └── DATA_FORMAT.md      # 저장 파일 및 CSV 형식
├── .gitignore
└── README.md               # 프로젝트 개요 및 요구사항
```

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
- [x] 예외 처리 데코레이터 1개 구현 및 적용

### CSV 가져오기 및 내보내기

- [x] `import --from <csv>`로 거래 일괄 등록
- [x] `export --out <csv> --month YYYY-MM`으로 월별 거래 내보내기
- [x] `export --out <csv> --from YYYY-MM-DD --to YYYY-MM-DD`로 기간별 거래 내보내기
- [x] 내보내기 시 `--month` 또는 `--from`·`--to` 조건 중 하나를 필수로 입력
- [x] 가져오기·내보내기 완료 후 처리 건수 출력
- [x] UTF-8 인코딩, 헤더 포함, 고정 CSV 스키마 적용

### 보너스 과제

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

### 사용자 가이드 (User Guide)

- [USER_GUIDE.md](docs/USER_GUIDE.md)
- [USER_DEMO.md](docs/USER_DEMO.md)

### 데이터 형식 (Data Format)

- [DATA_FORMAT.md](docs/DATA_FORMAT.md)
