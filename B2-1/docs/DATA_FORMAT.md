# 데이터 형식

## 저장 파일 위치 및 형식 (Data Storage)

- **기본 저장 위치**: `./data`
- **저장 형식**: JSONL 파일 5개, 한 줄당 JSON 객체 1개

| 파일 | 저장 내용 | 주요 필드 |
| --- | --- | --- |
| `data/transactions.jsonl` | 거래 내역 | `id`, `type`, `date`, `amount`, `category`, `memo`, `tags` |
| `data/categories.jsonl` | 사용 가능한 카테고리 | `name` |
| `data/budgets.jsonl` | 월별 예산 | `month`, `amount` |
| `data/recurring.jsonl` | 반복 거래 규칙 | `id`, `type`, `category`, `amount`, `day`, `memo`, `tags` |
| `data/sequences.jsonl` | 영구 ID 시퀀스 | `name`, `value` |

- **거래 저장 순서**: 날짜·ID 오름차순
- **목록·검색 순서**: 파일 역방향 읽기를 통한 날짜 최신순
- **ID 관리**: 별도 시퀀스 파일을 통한 거래·반복 규칙 삭제 후 ID 재사용 방지

거래 저장 예시:

```json
{"id":"TX-000012","type":"expense","date":"2024-01-15","amount":15000,"category":"food","memo":"점심","tags":["meal"]}
```

## Import/Export CSV 스키마

- 문자 인코딩: UTF-8
- 첫 번째 행: 헤더 필수
- `tags`: 태그가 여러 개인 경우 쉼표(`,`)로 구분
- 가져오기: 전체 행 선검증, 유효 행 원자적 일괄 반영, 잘못된 행 건너뛰기 및 건너뛴 건수 표시
- 내보내기: 데이터 저장 파일과의 경로 충돌 차단, 임시 파일 작성 후 결과 CSV 원자적 교체

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
