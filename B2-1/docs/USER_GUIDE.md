# 사용자 가이드

## 실행 방법 (Getting Started)

```bash
# 전체 도움말
python -m budget_app --help

# 명령별 도움말
python -m budget_app add --help

# 저장 폴더 직접 지정
python -m budget_app --data-dir ./data list --limit 10
```

- **기본 저장 폴더**: `./data`
- **저장 파일 초기화**: 파일·폴더 부재 시 자동 생성
- **기본 카테고리**: 카테고리 파일이 빈 경우 `food`, `transport`, `rent`, `salary`, `etc` 자동 생성
- **명령별 도움말**: 모든 명령에서 `--help` 지원
- **종료 코드**: 정상 종료 `0`, 오류 종료 `0` 이외

## 주요 명령 (Command Reference)

| 명령 | 설명 | 필수 입력 | 선택 입력 |
| --- | --- | --- | --- |
| `add` | 대화형 거래 추가 | 날짜, 타입, 카테고리, 금액 | 메모, 태그 |
| `list` | 날짜 최신순 거래 조회 | 없음 | `--limit N` (기본값: `20`) |
| `search` | 조건별 거래 검색 | 없음 | `--from`, `--to`, `--category`, `--type`, `--q`, `--tag` |
| `summary` | 월별 수입·지출·잔액 및 지출 순위 조회 | `--month YYYY-MM` | `--top N` (기본값: `3`) |
| `budget set` | 월 예산 설정 | `--month YYYY-MM`, `--amount <금액>` | 없음 |
| `budget get` | 월 예산 조회 | `--month YYYY-MM` | 없음 |
| `category add` | 카테고리 추가 | 카테고리명 대화형 입력 또는 `--name` | 없음 |
| `category list` | 카테고리 목록 조회 | 없음 | 없음 |
| `category remove` | 카테고리 삭제 | 카테고리명 대화형 입력 또는 `--name` | 없음 |
| `update` | ID 기준 거래 수정 | `--id <id>`, 수정 필드 최소 1개 | `--date`, `--type`, `--category`, `--amount`, `--memo`, `--tags` |
| `delete` | ID 기준 거래 삭제 | `--id <id>` | 없음 |
| `import` | CSV 거래 가져오기 | `--from <csv>` | 없음 |
| `export` | 조건별 거래 CSV 내보내기 | `--out <csv>`, `--month` 또는 `--from`·`--to` | 없음 |
| `backup` | 데이터 파일 ZIP 백업 | 없음 | `--out-dir <폴더>` (기본값: `./backups`) |
| `recurring add` | 반복 거래 규칙 추가 | `--type`, `--category`, `--amount`, `--day` | `--memo`, `--tags` |
| `recurring list` | 반복 거래 규칙 조회 | 없음 | 없음 |
| `recurring remove` | 반복 거래 규칙 삭제 | `--id <id>` | 없음 |
| `recurring generate` | 특정 월 반복 거래 생성 | `--month YYYY-MM` | 없음 |

## 명령 사용 예시

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

# 거래 수정 (옵션 기반)
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
