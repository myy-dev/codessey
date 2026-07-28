# FastAPI로 만드는 나만의 웹 애플리케이션

## 프로젝트 개요

FastAPI와 SQLAlchemy를 사용해 브라우저에서 데이터를 등록하고 조회·수정·삭제할 수 있는 웹 애플리케이션을 구현하는 프로젝트이다.

브라우저의 요청이 라우터, 서비스, 저장소, 데이터베이스를 거쳐 처리되고 Jinja2 템플릿을 통해 화면으로 반환되는 전체 흐름을 학습한다.

- 도메인 주제: 메모 관리
- 주요 기능: 메모 등록, 목록 조회, 상세 조회, 수정, 삭제
- 화면 렌더링 방식: Jinja2 기반 SSR
- 애플리케이션 구조: Router → Service → Repository → Database
- 데이터 저장 방식: SQLite + SQLAlchemy ORM

## 실행환경

Python 3.10 이상과 FastAPI를 사용한다. 데이터는 서버 메모리가 아닌 SQLite 데이터베이스 파일에 저장한다.

- 사용 언어: Python 3.10 이상
- 웹 프레임워크: FastAPI
- ASGI 서버: Uvicorn
- ORM: SQLAlchemy
- 템플릿 엔진: Jinja2
- 사용 DB: SQLite
- DB 파일 예시: `database.db`
- 서버 주소: `http://localhost:8000`

### 필수 패키지

외부 라이브러리는 다음 범위 내에서만 사용한다.

```text
fastapi
uvicorn
sqlalchemy
jinja2
python-multipart
```

### 제출물 구성

- [ ] 전체 프로젝트 소스코드
- [ ] 의존성 목록 파일(`requirements.txt` 또는 `pyproject.toml`)
- [ ] 실행 방법을 설명하는 `README.md`
- [ ] SQLite 데이터베이스 파일
- [ ] Jinja2 템플릿 파일
- [ ] 선택 사항: 주요 화면 스크린샷

## 프로젝트 구조

```text
B5-2/
├── README.md
├── requirements.txt
├── database.db
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── home.py
│   │   └── memos.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── memo_service.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── memo_repository.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── memo.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── memo.py
│   └── templates/
│       ├── base.html
│       ├── home.html
│       └── memos/
│           ├── list.html
│           ├── detail.html
│           ├── create.html
│           ├── edit.html
│           └── not_found.html
└── screenshots/
    ├── home.png
    ├── memo-list.png
    └── memo-detail.png
```

- `main.py`: FastAPI 애플리케이션 생성 및 라우터 등록
- `database.py`: SQLite 연결, 세션 생성, `Depends`용 DB 세션 함수 정의
- `routers/`: HTTP 요청 수신, 폼 데이터 처리, 템플릿 응답 및 리다이렉트
- `services/`: 입력값 검증과 같은 비즈니스 로직 처리
- `repositories/`: SQLAlchemy `Session`을 사용한 데이터베이스 CRUD
- `models/`: SQLAlchemy ORM 모델 정의
- `schemas/`: Pydantic 요청·응답 모델 또는 DTO 정의
- `templates/`: Jinja2 기반 HTML 템플릿
- `database.db`: 애플리케이션 데이터가 저장되는 SQLite 파일
- `screenshots/`: 선택 사항인 주요 화면 실행 결과

## 실행 순서

1. Python 가상환경을 생성한다.

```bash
python3 -m venv .venv
```

2. 가상환경을 활성화한다.

macOS 또는 Linux:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

3. 필요한 패키지를 설치한다.

```bash
pip install -r requirements.txt
```

4. FastAPI 애플리케이션을 실행한다.

```bash
uvicorn app.main:app --reload
```

5. 브라우저에서 다음 주소에 접속한다.

```text
http://localhost:8000
```

6. 터미널 로그에서 서버가 정상적으로 기동되었는지 확인한다.

```text
Uvicorn running on http://127.0.0.1:8000
```

7. 메모를 등록하고 목록, 상세, 수정, 삭제 흐름을 확인한다.

8. `database.db`를 DB Browser for SQLite 또는 Python 스크립트로 열어 데이터가 실제로 저장되었는지 확인한다.

## 주요 화면 및 URL

| 기능 | HTTP 방식 | URL | 처리 결과 |
|---|---|---|---|
| 홈 화면 | GET | `/` | 앱 소개와 주요 화면 링크 출력 |
| 메모 목록 | GET | `/memos` | 저장된 메모 목록 출력 |
| 메모 등록 화면 | GET | `/memos/new` | 등록 폼 출력 |
| 메모 등록 처리 | POST | `/memos` | 저장 후 상세 또는 목록으로 리다이렉트 |
| 메모 상세 | GET | `/memos/{memo_id}` | 메모 전체 필드 출력 |
| 메모 수정 화면 | GET | `/memos/{memo_id}/edit` | 기존 값이 포함된 수정 폼 출력 |
| 메모 수정 처리 | POST | `/memos/{memo_id}/edit` | 수정 후 상세 화면으로 리다이렉트 |
| 메모 삭제 처리 | POST | `/memos/{memo_id}/delete` | 삭제 후 목록 화면으로 리다이렉트 |

등록·수정·삭제 이후에는 `RedirectResponse`와 `status_code=303`을 사용해 PRG(Post-Redirect-Get) 패턴을 적용한다.

## 요청 처리 흐름

```text
브라우저 요청
    ↓
Router
요청 데이터 수신 및 응답 결정
    ↓
Service
입력값 검증 및 비즈니스 규칙 처리
    ↓
Repository
SQLAlchemy Session을 이용한 DB 접근
    ↓
SQLite Database
데이터 저장·조회·수정·삭제
    ↓
Jinja2 Template
HTML 화면 렌더링
    ↓
브라우저 응답
```

- 라우터는 HTTP 요청과 응답 및 화면 전환에 집중한다.
- 서비스는 필수값 검사와 같은 비즈니스 로직을 처리한다.
- 저장소는 데이터베이스 CRUD만 담당한다.
- 템플릿은 전달받은 데이터를 HTML 화면으로 표현한다.

## 수행 항목 체크리스트

### 개발 환경 준비

- [ ] Python 3.10 이상 설치 확인
- [ ] Python 가상환경 생성 및 활성화
- [ ] `requirements.txt` 또는 `pyproject.toml` 작성
- [ ] 필수 패키지 설치
- [ ] FastAPI 서버 실행
- [ ] `http://localhost:8000` 접속 확인
- [ ] 터미널에서 서버 정상 기동 로그 확인

### 프로젝트 구조

- [ ] `routers/` 디렉터리 구성
- [ ] `services/` 디렉터리 구성
- [ ] `repositories/` 디렉터리 구성
- [ ] `models/` 디렉터리 구성
- [ ] `templates/` 디렉터리 구성
- [ ] 라우터, 서비스, 저장소, 모델 코드 역할 분리
- [ ] 애플리케이션 시작 파일 작성

### 홈 화면

- [ ] `GET /` 라우트 구현
- [ ] Jinja2 `TemplateResponse`로 홈 화면 렌더링
- [ ] 앱의 목적을 설명하는 문장 1~2줄 작성
- [ ] 메모 목록으로 이동하는 링크 작성
- [ ] 메모 등록 화면으로 이동하는 링크 작성
- [ ] 홈 화면에 최소 2개 이상의 링크 제공

### 메모 모델 설계

- [ ] 단일 SQLAlchemy ORM 모델 작성
- [ ] 메모 기본키 필드 정의
- [ ] 제목 필드 정의
- [ ] 내용 필드 정의
- [ ] 작성일시 필드 정의
- [ ] 필요하면 수정일시 필드 정의
- [ ] 각 필드에 적절한 SQLAlchemy 타입 적용
- [ ] 필수 필드에 `nullable=False` 적용
- [ ] 모델의 전체 필드를 상세 화면에 표시

메모 모델 필드 예시는 다음과 같다.

| 필드 | 역할 | 타입 예시 |
|---|---|---|
| `id` | 메모 식별자 | Integer, Primary Key |
| `title` | 메모 제목 | String |
| `content` | 메모 내용 | Text |
| `created_at` | 작성일시 | DateTime |
| `updated_at` | 수정일시 | DateTime |

### SQLite 및 SQLAlchemy 연결

- [ ] SQLite 연결 URL 설정
- [ ] SQLAlchemy 엔진 및 세션 팩토리 생성
- [ ] ORM Base 클래스 구성
- [ ] 애플리케이션 실행 시 테이블 생성
- [ ] FastAPI `Depends`를 이용한 DB 세션 주입
- [ ] 요청 종료 후 세션이 닫히도록 처리
- [ ] 프로젝트 디렉터리에 `database.db` 생성 확인
- [ ] DB Browser for SQLite 등으로 저장 데이터 확인

### 메모 목록 조회

- [ ] `GET /memos` 구현
- [ ] 저장소에 전체 메모 조회 기능 작성
- [ ] 서비스를 통해 메모 목록 조회
- [ ] 목록 화면을 Jinja2 템플릿으로 렌더링
- [ ] 각 메모의 제목과 상세 화면 링크 표시
- [ ] 새 메모 등록 화면 링크 제공
- [ ] 등록된 메모가 없을 때 안내 문구 표시

### 메모 상세 조회

- [ ] `GET /memos/{memo_id}` 구현
- [ ] 저장소에 ID 기반 단건 조회 기능 작성
- [ ] 서비스를 통해 메모 단건 조회
- [ ] 상세 화면에 메모 전체 필드 표시
- [ ] 수정 화면으로 이동하는 링크 또는 버튼 제공
- [ ] 삭제 버튼 제공
- [ ] 목록으로 돌아가는 링크 제공
- [ ] 존재하지 않는 메모 조회 시 안내 화면 또는 목록 리다이렉트 적용

### 메모 등록

- [ ] `GET /memos/new` 등록 화면 구현
- [ ] 제목 및 내용 입력 필드 작성
- [ ] 저장 버튼과 취소 링크 작성
- [ ] 등록 폼의 전송 방식을 POST로 지정
- [ ] FastAPI `Form()`으로 입력값 수신
- [ ] 서비스에 메모 등록 로직 작성
- [ ] 저장소에 ORM 기반 INSERT 기능 작성
- [ ] 등록 완료 후 `RedirectResponse` 사용
- [ ] 등록 리다이렉트에 `status_code=303` 적용
- [ ] 새로고침 시 중복 등록이 발생하지 않는지 확인

### 메모 수정

- [ ] `GET /memos/{memo_id}/edit` 수정 화면 구현
- [ ] 수정 폼에 기존 메모 값 표시
- [ ] 저장 버튼과 취소 링크 작성
- [ ] 수정 폼의 전송 방식을 POST로 지정
- [ ] FastAPI `Form()`으로 수정값 수신
- [ ] 서비스에 메모 수정 로직 작성
- [ ] 저장소에 ORM 기반 UPDATE 기능 작성
- [ ] 수정 완료 후 `RedirectResponse` 사용
- [ ] 수정 리다이렉트에 `status_code=303` 적용
- [ ] 존재하지 않는 메모 수정 요청 처리

### 메모 삭제

- [ ] `POST /memos/{memo_id}/delete` 구현
- [ ] 상세 화면에 삭제 버튼 작성
- [ ] 삭제 요청을 POST 방식으로 처리
- [ ] 서비스에 메모 삭제 로직 작성
- [ ] 저장소에 ORM 기반 DELETE 기능 작성
- [ ] 삭제 완료 후 목록 화면으로 HTTP 303 리다이렉트
- [ ] 존재하지 않는 메모 삭제 요청 처리

### SSR 및 템플릿

- [ ] 공통 레이아웃 템플릿 작성
- [ ] 홈, 목록, 상세, 등록, 수정 템플릿 작성
- [ ] 오류 또는 데이터 없음 안내 화면 작성
- [ ] 모든 주요 GET 화면에서 `TemplateResponse` 사용
- [ ] 템플릿에 `request` 객체 전달
- [ ] 화면 사이를 이동할 수 있는 링크 구성

### 레이어 분리

- [ ] 라우터는 요청 데이터 수신과 응답 생성만 담당
- [ ] 라우터에서 SQLAlchemy 조회문 직접 작성 금지
- [ ] 서비스에 입력 검증과 비즈니스 로직 작성
- [ ] 저장소에 데이터 접근 로직 작성
- [ ] 저장소에서 SQLAlchemy `Session` 사용
- [ ] 모델에 SQLAlchemy ORM 테이블 정의
- [ ] FastAPI `Depends`로 DB 세션 전달
- [ ] 필요한 경우 Pydantic Schema 또는 DTO로 데이터 분리

### PRG 패턴

- [ ] 등록·수정·삭제 요청을 POST로 처리
- [ ] 각 POST 처리 이후 GET 화면으로 리다이렉트
- [ ] 모든 POST 리다이렉트에 HTTP 303 적용
- [ ] 리다이렉트 후 새로고침 테스트
- [ ] 새로고침으로 데이터가 중복 처리되지 않는지 확인

## 보너스 과제

### 메모 검색 기능

- [ ] 목록 화면에 검색 입력 필드 추가
- [ ] 검색 폼을 GET 방식으로 처리
- [ ] 쿼리 파라미터로 검색어 수신
- [ ] 제목에 검색어가 포함된 메모 조회
- [ ] SQLAlchemy `filter()` 또는 `like()` 사용
- [ ] 검색 결과가 없을 때 안내 문구 표시
- [ ] 검색어를 비우면 전체 목록 표시

검색 URL 예시는 다음과 같다.

```text
GET /memos?q=FastAPI
```

### 서버 사이드 검증

- [ ] 제목 및 내용 필수값 검증
- [ ] 공백만 입력한 값이 저장되지 않도록 처리
- [ ] 검증 로직을 서비스 계층에 작성
- [ ] 검증 실패 시 폼 화면과 안내 문구 표시
- [ ] 기존 입력값이 폼에서 유지되도록 처리
- [ ] 잘못된 데이터가 DB에 저장되지 않는지 확인

### 수정 및 삭제 UX 개선

- [ ] 상세 화면에서 수정 화면으로 자연스럽게 이동
- [ ] 상세 화면에 삭제 버튼 배치
- [ ] 삭제 전 확인 메시지 제공
- [ ] 작업 완료 후 적절한 화면으로 이동
- [ ] 목록·상세·등록·수정 화면 사이의 이동 경로 구성

## 제약 사항

- [ ] Python 3.10 이상 사용
- [ ] FastAPI, Uvicorn, SQLAlchemy, Jinja2, python-multipart 사용
- [ ] 지정된 필수 패키지 외 외부 라이브러리 추가 금지
- [ ] 서버 메모리 리스트 또는 딕셔너리만으로 데이터 관리 금지
- [ ] SQLite 데이터베이스에 데이터 저장
- [ ] 라우터, 서비스, 저장소, 모델 역할 분리
- [ ] 등록 및 수정 폼에 POST 방식 사용
- [ ] 폼 데이터는 FastAPI `Form()`으로 수신
- [ ] 등록·수정·삭제 이후 HTTP 303 리다이렉트 적용
- [ ] DB 세션은 FastAPI `Depends`로 관리
- [ ] 로그인, 인증 및 권한 기능 구현 금지
- [ ] 모델 간 연관관계 구현 금지
- [ ] 단일 모델의 CRUD 범위 유지
- [ ] 주요 화면은 Jinja2 `TemplateResponse`로 출력

## 결과 확인 자료

- [ ] 홈 화면에서 앱 목적 문구와 주요 링크 확인
- [ ] 등록 폼으로 새 메모 저장 확인
- [ ] 등록된 메모가 목록에 표시되는지 확인
- [ ] 메모 상세 화면에서 전체 필드 확인
- [ ] 기존 메모 수정 결과 확인
- [ ] 메모 삭제 결과 확인
- [ ] 존재하지 않는 메모 조회 처리 확인
- [ ] 등록·수정·삭제 응답의 HTTP 303 확인
- [ ] POST 이후 새로고침 시 중복 요청이 발생하지 않는지 확인
- [ ] 서버 재시작 후에도 데이터가 유지되는지 확인
- [ ] `database.db`에서 저장된 행 직접 확인
- [ ] 라우터 → 서비스 → 저장소 호출 구조 확인
- [ ] 선택 사항으로 주요 화면 스크린샷 저장

## 학습 결과 확인

프로젝트 완료 후 다음 내용을 자신의 코드 구조를 근거로 설명할 수 있어야 한다.

- [ ] 브라우저 요청이 라우터, 서비스, 저장소, DB를 거쳐 처리되는 과정
- [ ] DB 조회 결과가 Jinja2 템플릿을 통해 HTML로 반환되는 과정
- [ ] GET 요청과 POST 요청의 역할 차이
- [ ] HTML Form 데이터가 FastAPI `Form()`으로 전달되는 과정
- [ ] PRG 패턴을 적용하는 이유
- [ ] POST 리다이렉트에서 HTTP 303을 사용하는 이유
- [ ] SQLAlchemy ORM 모델과 데이터베이스 테이블의 관계
- [ ] SQLAlchemy `Session`으로 CRUD를 처리하는 방법
- [ ] FastAPI `Depends`로 DB 세션을 관리하는 이유
- [ ] 라우터, 서비스, 저장소를 분리했을 때 얻는 유지보수상의 장점
