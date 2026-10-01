# 전체 기능 사용자 시연

## 1~9 자동 실행

`./data` 폴더가 없는 상태에서 프로젝트 루트에서 실행

```bash
bash scripts/user_demo.sh
```

각 명령어를 `$ 명령어` 형식으로 먼저 표시한 뒤 실행 결과 출력

1~9번 자동 실행 완료 후 10번 CSV와 11번 ZIP 백업 수동 시연

## 1. 최초 상태 및 자동 초기화 확인

프로젝트 루트의 `./data` 폴더가 없는 상태

### 전체 도움말 확인

```bash
python3 -m budget_app --help
```

### 저장 파일 자동 생성 및 기본 카테고리 확인

```bash
python3 -m budget_app category list
```

`transactions.jsonl`, `categories.jsonl`, `budgets.jsonl`, `recurring.jsonl`, `sequences.jsonl` 생성 확인

### 빈 거래 안내 확인

```bash
python3 -m budget_app list
```

## 2. 카테고리 추가

### 카테고리 등록

```bash
python3 -m budget_app category add --name hobby
```

### 카테고리 목록 확인

```bash
python3 -m budget_app category list
```

## 3. 거래 추가

`add`의 대화형 입력 순서: 날짜 → 타입 → 카테고리 → 금액 → 메모 → 태그

### 첫 지출 등록

자동 생성 ID `TX-000001`

```bash
python3 -m budget_app add <<'EOF'
2024-01-15
expense
food
15000
점심
meal
EOF
```

### 수입 거래 등록

자동 생성 ID `TX-000002`

```bash
python3 -m budget_app add <<'EOF'
2024-01-25
income
salary
3000000
월급
salary,monthly
EOF
```

### 추가 지출 거래 등록

자동 생성 ID `TX-000003`

```bash
python3 -m budget_app add <<'EOF'
2024-01-20
expense
hobby
7000
책
book
EOF
```

### 거래 추가 후 월별 요약 확인

2024년 1월 총수입 3,000,000원, 총지출 22,000원, 잔액 2,978,000원 확인

```bash
python3 -m budget_app summary --month 2024-01 --top 3
```

## 4. 거래 목록 및 검색

### 최근 거래 개수 제한

```bash
python3 -m budget_app list --limit 2
```

### 전체 거래 목록 확인

```bash
python3 -m budget_app list --limit 10
```

### 기간·카테고리·타입 검색

```bash
python3 -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food --type expense
```

### 메모·태그 검색

```bash
python3 -m budget_app search --q 점심 --tag meal
```

## 5. 예산 설정 및 월별 요약

### 월 예산 설정

```bash
python3 -m budget_app budget set --month 2024-01 --amount 10000
```

### 월 예산 조회

```bash
python3 -m budget_app budget get --month 2024-01
```

### 예산 사용률 및 초과 여부 확인

2024년 1월 지출 22,000원, 예산 10,000원, 예산 초과 경고 및 카테고리별 지출 순위 확인

```bash
python3 -m budget_app summary --month 2024-01 --top 3
```

## 6. 거래 수정

ID는 거래 추가 시 자동 생성된 값

### 날짜·금액·메모·태그 수정

```bash
python3 -m budget_app update --id TX-000001 --date 2024-01-16 --amount 18000 --memo "저녁" --tags dinner
```

### 수정 결과 검색

```bash
python3 -m budget_app search --q 저녁 --tag dinner
```

## 7. 카테고리 삭제 제한 및 삭제

### 사용 중인 카테고리 삭제 시도

```bash
python3 -m budget_app category remove --name hobby
```

### 오류 종료 코드 확인

스택트레이스 없는 오류·해결 힌트와 종료 코드 `2` 확인

```bash
echo $?
```

### 카테고리 사용 거래 변경

`TX-000003` 거래의 타입을 `income`, 카테고리를 `salary`로 변경

```bash
python3 -m budget_app update --id TX-000003 --type income --category salary
python3 -m budget_app list --limit 10
```

### 미사용 카테고리 삭제

```bash
python3 -m budget_app category remove --name hobby
python3 -m budget_app category list
```

## 8. 거래 삭제

### 거래 삭제

```bash
python3 -m budget_app delete --id TX-000003
```

### 삭제 결과 확인

```bash
python3 -m budget_app list --limit 10
```

## 9. 반복 거래 등록·생성·삭제

### 반복 거래 규칙 등록

자동 생성 규칙 ID `RC-000001`

```bash
python3 -m budget_app recurring add --type expense --category rent --amount 500000 --day 31 --memo "월세"
```

### 반복 거래 규칙 목록 확인

```bash
python3 -m budget_app recurring list
```

### 2024년 2월 반복 거래 생성 및 ID 미재사용 확인

31일 규칙의 2024년 2월 29일 날짜 보정과 거래 ID `TX-000004` 확인

```bash
python3 -m budget_app recurring generate --month 2024-02
python3 -m budget_app search --from 2024-02-01 --to 2024-02-29 --category rent
```

첫 생성 결과 `created=1, skipped=0`

### 같은 달 중복 생성 방지 확인

```bash
python3 -m budget_app recurring generate --month 2024-02
```

두 번째 생성 결과 `created=0, skipped=1`

### 반복 거래 규칙 삭제

```bash
python3 -m budget_app recurring remove --id RC-000001
python3 -m budget_app recurring list
```

### 생성된 거래 유지 확인

```bash
python3 -m budget_app search --from 2024-02-01 --to 2024-02-29 --category rent
```

## 10. CSV 내보내기 및 가져오기

### 월별 거래 내보내기

2024년 1월 거래 2건 내보내기

```bash
python3 -m budget_app export --out demo-january.csv --month 2024-01
```

### 기간별 거래 내보내기

2024년 2월 거래 1건 내보내기

```bash
python3 -m budget_app export --out demo-february.csv --from 2024-02-01 --to 2024-02-29
```

### CSV 파일 확인

VS Code에서 `demo-january.csv`를 열어 헤더 `date,type,category,amount,memo,tags`와 한글 데이터 확인

### 내보낸 CSV에 신규 거래 추가

VS Code에서 `demo-january.csv`의 기존 거래 2건 아래에 새 거래 2건 추가

기존 헤더 유지, 새 헤더 추가 없음

```csv
2024-01-10,expense,transport,2500,버스,commute
2024-01-28,expense,food,12000,저녁,meal
```

### CSV 거래 가져오기

기존 거래 2건과 새 거래 2건을 새로운 ID로 다시 등록

```bash
python3 -m budget_app import --from demo-january.csv
```

처리 결과 `imported=4, skipped=0`

- 기존 거래 복사본: `TX-000005`, `TX-000006`
- 새 거래: `TX-000007`, `TX-000008`

### 가져오기 결과 확인

```bash
python3 -m budget_app list --limit 10
```

## 11. ZIP 백업 및 내용 확인

### 데이터 백업 생성

현재 `./data`의 영구 저장 파일 5개를 타임스탬프 포함 ZIP 파일로 백업

```bash
python3 -m budget_app backup --out-dir ./backups
```

**참고 문서**: [사용자 가이드](USER_GUIDE.md), [데이터 형식](DATA_FORMAT.md)
