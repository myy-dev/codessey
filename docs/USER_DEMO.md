# 사용자 시연 예시

## 최초 실행 및 빈 데이터 확인

```bash
python3 -m budget_app --help
python3 -m budget_app category list
python3 -m budget_app list
python3 -m budget_app summary --month 2024-01
```

## 카테고리 추가

```bash
python3 -m budget_app category add --name hobby
python3 -m budget_app category list
```

## 거래 추가

`add`의 대화형 입력 순서: 날짜 → 타입 → 카테고리 → 금액 → 메모 → 태그. 첫 거래의 잘못된 날짜 입력 후 재입력 시연. 저장 완료 메시지의 자동 생성 ID: 순서대로 `TX-000001`, `TX-000002`, `TX-000003`.

```bash
python3 -m budget_app add <<'EOF'
2024-13-40
2024-01-15
expense
food
15000
점심
meal
EOF

python3 -m budget_app add <<'EOF'
2024-01-25
income
salary
3000000
월급
salary,monthly
EOF

python3 -m budget_app add <<'EOF'
2024-01-20
expense
hobby
7000
책
book
EOF
```

## 거래 목록 및 검색

날짜 최신순 목록, 기간·카테고리·타입 검색, 메모·태그 검색. `--data-dir` 옵션도 기본 저장 폴더를 지정하는 방식으로 확인.

```bash
python3 -m budget_app list --limit 2
python3 -m budget_app --data-dir ./data list --limit 10
python3 -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food --type expense
python3 -m budget_app search --q 점심 --tag meal
```

## 예산 설정 및 월별 요약

2024년 1월 지출 22,000원, 예산 10,000원, 예산 초과 경고 및 카테고리별 지출 순위 확인.

```bash
python3 -m budget_app budget set --month 2024-01 --amount 10000
python3 -m budget_app budget get --month 2024-01
python3 -m budget_app summary --month 2024-01 --top 3
```

## 거래 수정

첫 거래의 날짜·금액·메모·태그 수정. ID는 사용자가 지정하는 값이 아니라 거래 추가 시 자동 생성된 값.

```bash
python3 -m budget_app update --id TX-000001 --date 2024-01-16 --amount 18000 --memo "저녁" --tags dinner
python3 -m budget_app search --q 저녁 --tag dinner
```

## 카테고리 삭제 제한 및 삭제

`hobby` 사용 중 삭제 시도 → 오류·해결 힌트 출력. 해당 거래의 타입과 카테고리를 변경한 뒤 삭제 성공.

```bash
python3 -m budget_app category remove --name hobby
python3 -m budget_app update --id TX-000003 --type income --category salary
python3 -m budget_app list --limit 10
python3 -m budget_app category remove --name hobby
python3 -m budget_app category list
```

## 거래 삭제

세 번째 거래 삭제 후 목록·요약 변경 확인. 삭제한 ID의 재사용 없음.

```bash
python3 -m budget_app delete --id TX-000003
python3 -m budget_app list --limit 10
python3 -m budget_app summary --month 2024-01 --top 3
```

## 반복 거래 등록·생성·삭제

자동 생성 규칙 ID `RC-000001`. 31일 규칙의 2024년 2월 29일 날짜 보정, 같은 달 재생성 시 중복 건너뛰기 확인.

```bash
python3 -m budget_app recurring add --type expense --category rent --amount 500000 --day 31 --memo "월세"
python3 -m budget_app recurring list
python3 -m budget_app recurring generate --month 2024-02
python3 -m budget_app search --from 2024-02-01 --to 2024-02-29 --category rent
python3 -m budget_app recurring generate --month 2024-02
python3 -m budget_app recurring remove --id RC-000001
python3 -m budget_app recurring list
```

## CSV 내보내기 및 가져오기

월별 내보내기 2건, 기간별 내보내기 1건. 1월 CSV 재가져오기 시 동일 내용의 거래 2건 추가 및 새 ID 부여.

```bash
python3 -m budget_app export --out demo-january.csv --month 2024-01
python3 -m budget_app export --out demo-february.csv --from 2024-02-01 --to 2024-02-29
python3 -m budget_app import --from demo-january.csv
python3 -m budget_app list --limit 10
```

## 데이터 백업

현재 `./data`의 영구 저장 파일 5개를 타임스탬프가 포함된 ZIP 파일로 백업.

```bash
python3 -m budget_app backup --out-dir ./backups
```

**참고 문서**: [사용자 가이드](USER_GUIDE.md), [데이터 형식](DATA_FORMAT.md)
