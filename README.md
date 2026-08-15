# SQL로 만드는 나만의 데이터베이스

## 프로젝트 개요

SQL만 사용해 도메인 데이터베이스를 설계하고 데이터를 입력한 뒤, 핵심 요구사항을 쿼리로 해결하는 데이터베이스 기초 실습 프로젝트이다.

- 도메인 주제: 온라인 서점 주문 관리

## 실행환경

SQLite를 사용한다. SQLite는 별도 DB 서버 없이 파일 기반으로 동작하므로 설치와 실행이 간단하고, SQL 기초 실습에 적합하다.

- 사용 DB: SQLite
- DB 파일 예시: `database.db`
- SQL 실행 도구 권장: DB Browser for SQLite
- 보조 실행 도구: `sqlite3` CLI

SQL 실행도구는 GUI 기반인 DB Browser for SQLite를 기본으로 사용한다. 테이블 구조와 데이터를 눈으로 확인하기 쉽고, 쿼리 실행 결과를 `results/`에 정리하기 편하다.

터미널 사용에 익숙한 경우 `sqlite3 database.db` 명령으로 SQL 파일을 직접 실행해도 된다. SQLite 고유 문법을 사용한 경우 해당 SQL 파일에 주석으로 SQLite 전용 문법임을 명시한다.

### 제출물 구성

- [x] 스키마 생성 SQL 파일 1개
- [x] 샘플 데이터 INSERT SQL 파일 1개
- [x] 핵심 쿼리 15개 이상 포함 SQL 파일 1개
- [x] 실행 결과 자료 폴더 1개
- [x] ERD 다이어그램 이미지 1개(draw.io, dbdiagram.io 등 활용)

## 프로젝트 구조

```text
B5-1/
├── README.md
├── schema.sql
├── data.sql
├── queries.sql
├── bonus.md
├── results/
│   ├── query-01.txt
│   ├── query-02.txt
│   └── query-20.txt
└── erd/
    └── erd.png
```

- `schema.sql`: 테이블 생성, PK/FK, 제약조건 정의
- `data.sql`: 각 테이블별 샘플 데이터 INSERT
- `queries.sql`: 핵심 SQL 쿼리 15개 이상과 쿼리별 설명
- `bonus.md`: 보너스 과제 비교, FK 오류 원인, 미니 리포트 정리
- `results/`: 쿼리 실행 결과 자료
- `erd/`: ERD 다이어그램 이미지

## 실행 순서

### SQLite CLI 실습용 실행

프로젝트 폴더에서 SQLite CLI를 실행한다.

```bash
sqlite3 database.db
```

SQLite CLI에 접속한 뒤 출력 형식을 설정하고 스키마와 샘플 데이터를 불러온다.

```sql
.headers on
.mode column
.read schema.sql
.read data.sql
```

준비가 끝나면 `queries.sql`의 Query 01부터 필요한 쿼리를 하나씩 실행한다.

1. `schema.sql`로 테이블과 제약조건을 생성한다.
2. `data.sql`로 샘플 데이터를 입력한다.
3. `queries.sql`의 Query 01~20을 실행한다.
4. `results/query-XX.txt`에서 쿼리별 확인 목적, 실행 SQL, 결과를 확인한다.
5. Query 19는 FK 오류 확인용 쿼리이므로 `FOREIGN KEY constraint failed`가 정상 결과이다.

## 수행 항목 체크리스트

### DB 환경 준비

- [x] SQLite 설치 또는 준비
- [x] DB Browser for SQLite 또는 `sqlite3` CLI 준비
- [x] 사용 DB 종류를 SQLite로 명시
- [x] DB 고유 문법 사용 시 쿼리 주석 작성

### 데이터 모델 설계

- [x] 자유 주제 1개 선정
- [x] 최소 4개 이상 테이블 설계
- [x] 각 테이블 PK 정의
- [x] 최소 2개 이상 FK 사용
- [x] 최소 2개 이상 1:N 관계 포함
- [x] 의미에 맞는 컬럼 타입 선택
- [x] 역할이 드러나는 테이블명과 컬럼명 작성

### 제약조건 적용

- [x] 최소 1개 컬럼 `NOT NULL` 적용
- [x] 최소 1개 컬럼 `UNIQUE` 적용
- [x] FK 동작 설정
- [x] 존재하지 않는 부모 데이터 참조 INSERT 차단 확인

### 샘플 데이터 준비

- [x] 각 테이블 최소 10행 이상 데이터 입력
- [x] FK 관계가 반영된 데이터 입력
- [x] 부모 테이블 입력 후 자식 테이블 입력
- [x] 도메인 주제에 맞는 의미 있는 데이터 구성

### 핵심 SQL 쿼리 작성

- [x] 총 15개 이상 핵심 SQL 쿼리 작성
- [x] 기본 조회 쿼리 4개 이상 작성
- [x] 기본 조회에 `WHERE`, `ORDER BY`, `LIMIT` 포함
- [x] 조인 쿼리 4개 이상 작성
- [x] `INNER JOIN` 2개 이상 작성
- [x] `LEFT JOIN` 1개 이상 작성
- [x] 집계 쿼리 3개 이상 작성
- [x] `COUNT`, `SUM`, `AVG` 중 2개 이상 사용
- [x] 집계 쿼리에 `GROUP BY` 포함
- [x] 서브쿼리 1개 이상 작성
- [x] 수정 및 삭제 쿼리 2개 이상 작성
- [x] `CREATE INDEX` 1개 이상 작성
- [x] 인덱스 적용 이유 1줄 설명

### 보너스 과제

#### 조인 1개를 두 방식으로 풀기

- [x] 같은 요구사항의 `JOIN` 방식 해결
- [x] 같은 요구사항의 서브쿼리 방식 해결
- [x] 두 방식 차이 비교 기록

#### 데이터 정합성 깨뜨려 보기

- [x] FK 오류 발생 INSERT 시도
- [x] 오류 발생 원인 기록
- [x] 올바른 입력 방식 기록

#### 미니 리포트 만들기

- [x] 핵심 지표 3개 정의
- [x] 각 지표 산출 SQL 작성
- [x] 최종 리포트 형태의 쿼리와 결과 정리

## 제약 사항

- [x] 백엔드 프레임워크 사용 금지
- [x] Spring, Django, Express 기반 API 또는 화면 구현 금지
- [x] 로컬 실행 가능 DB만 사용
- [x] 실행 순서가 드러나는 제출 파일 정리
- [x] 스키마, 데이터, 쿼리, 실행 결과 자료 포함
- [x] DB, 주제, 테이블 명명 규칙 일관성 유지
- [x] 작성 테이블 또는 쿼리 역할 설명 가능
- [x] PK, FK, 1:N 관계 연결 방식 설명 가능
- [x] `SELECT`, `INSERT`, `UPDATE`, `DELETE` 사용 목적 구분
- [x] `JOIN`과 `GROUP BY` 기반 연결 데이터 조회 방식 설명 가능
- [x] 검색, 정렬, 집계, 랭킹 요구사항의 SQL 해결 과정 설명 가능
- [x] 인덱스 적용 컬럼과 이유 설명 가능
- [x] 뷰, 프로시저, 트리거 등 고급 기능 사용 금지
- [x] 과도한 정규화 이론보다 자연스러운 관계와 쿼리 가능성 우선

### 결과 확인 자료

- [x] 각 쿼리별 확인 목적 1줄 설명
- [x] 각 쿼리 실행 결과 저장
- [x] 쿼리 번호와 결과 파일명 매칭
- [x] 쿼리와 결과 자료만으로 실행 내용 확인 가능 구성
