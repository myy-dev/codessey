# 글을 쓰고·보고·고치고·지울 수 있는 게시판형 웹 서비스 만들기

## 프로젝트 개요

FastAPI와 SQLAlchemy를 사용해 브라우저에서 데이터를 등록하고 조회·수정·삭제할 수 있는 웹 애플리케이션 구현 프로젝트

## 기술 스택

| 구분           | 기술             |
| -------------- | ---------------- |
| 언어           | Python 3.10 이상 |
| 웹 프레임워크  | FastAPI          |
| ASGI 서버      | Uvicorn          |
| ORM            | SQLAlchemy       |
| 데이터베이스   | SQLite           |
| 서버 템플릿    | Jinja2           |
| 화면 구성      | HTML, CSS        |
| 폼 데이터 파싱 | python-multipart |

## 실행

```sh
uv run uvicorn app.main:app --reload
```

## 프로젝트 구조

```text
B6-2/
├── .gitignore
├── README.md
├── pyproject.toml            # 프로젝트 정보 및 직접 의존성
├── uv.lock                   # 전체 의존성 버전 고정
├── .python-version           # 개발용 Python 버전
├── database.db                # 애플리케이션 데이터가 저장되는 SQLite 파일
├── docs/                      # 화면·URL 참조 및 구조 설명 문서
│   ├── routes.md
│   └── architecture.md
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI 애플리케이션 생성 및 라우터 등록
│   ├── database.py            # SQLite 연결, 세션 생성, Depends용 DB 세션 함수 정의
│   ├── templating.py          # Jinja2 템플릿 설정 및 스타일시트 버전 관리
│   ├── routers/               # HTTP 요청 수신, 폼 데이터 처리, 템플릿 응답 및 리다이렉트
│   │   ├── __init__.py
│   │   ├── home.py
│   │   └── memos.py
│   ├── services/              # 도메인 규칙과 CRUD 작업 흐름 등 비즈니스 로직 처리
│   │   ├── __init__.py
│   │   └── memo_service.py
│   ├── repositories/          # SQLAlchemy Session을 사용한 데이터베이스 CRUD
│   │   ├── __init__.py
│   │   └── memo_repository.py
│   ├── models/                # SQLAlchemy ORM 모델 정의
│   │   ├── __init__.py
│   │   └── memo.py
│   ├── schemas/               # dataclass 기반 폼 입력값 및 DTO 정의
│   │   ├── __init__.py
│   │   └── memo.py
│   ├── templates/             # Jinja2 기반 HTML 템플릿
│   │   ├── base.html
│   │   ├── home.html
│   │   └── memos/
│   │       ├── _form.html
│   │       ├── list.html
│   │       ├── detail.html
│   │       ├── create.html
│   │       ├── edit.html
│   │       └── not_found.html
│   └── static/                # 화면 스타일시트
│       ├── styles.css
│       └── favicon.svg
└── tests/                     # 서비스·템플릿 테스트 및 실제 서버 HTTP 스모크 테스트
    ├── __init__.py
    ├── test_memo_service.py
    ├── test_templating.py
    └── http_smoke.py
```

## 수행 항목 체크리스트

### 개발 환경 준비

- [x] Python 3.10 이상 설치 확인
- [x] Python 가상환경 생성 및 활성화
- [x] `requirements.txt` 또는 `pyproject.toml` 작성
- [x] 필수 패키지 설치
- [x] FastAPI 서버 실행
- [x] `http://localhost:8000` 접속 확인
- [x] 터미널에서 서버 정상 기동 로그 확인

### 프로젝트 구조

- [x] `routers/` 디렉터리 구성
- [x] `services/` 디렉터리 구성
- [x] `repositories/` 디렉터리 구성
- [x] `models/` 디렉터리 구성
- [x] `templates/` 디렉터리 구성
- [x] 라우터, 서비스, 저장소, 모델 코드 역할 분리
- [x] 애플리케이션 시작 파일 작성

### 홈 화면

- [x] `GET /` 라우트 구현
- [x] Jinja2 `TemplateResponse`로 홈 화면 렌더링
- [x] 앱의 목적을 설명하는 문장 1~2줄 작성
- [x] 메모 목록으로 이동하는 링크 작성
- [x] 메모 등록 화면으로 이동하는 링크 작성
- [x] 홈 화면에 최소 2개 이상의 링크 제공

### 메모 모델 설계

- [x] 단일 SQLAlchemy ORM 모델 작성
- [x] 메모 기본키 필드 정의
- [x] 제목 필드 정의
- [x] 내용 필드 정의
- [x] 작성일시 필드 정의
- [x] 선택 사항으로 수정일시 필드 정의
- [x] 각 필드에 적절한 SQLAlchemy 타입 적용
- [x] 선택한 필수 필드에 `nullable=False` 적용
- [x] 모델의 전체 필드를 상세 화면에 표시

### SQLite 및 SQLAlchemy 연결

- [x] SQLite 연결 URL 설정
- [x] SQLAlchemy 엔진 및 세션 팩토리 생성
- [x] ORM Base 클래스 구성
- [x] FastAPI `Depends`를 이용한 DB 세션 주입
- [x] 프로젝트 디렉터리에 `database.db` 생성 확인
- [x] DB Browser for SQLite 등으로 저장 데이터 확인
- [x] 구현 방식에 따라 애플리케이션 실행 시 테이블 생성
- [x] 권장: 요청 종료 후 DB 세션이 닫히도록 처리

### 메모 목록 조회

- [x] `GET /memos` 구현
- [x] 저장소에 전체 메모 조회 기능 작성
- [x] 서비스를 통해 메모 목록 조회
- [x] 목록 화면을 Jinja2 템플릿으로 렌더링
- [x] 각 메모의 제목과 상세 화면 링크 표시
- [x] 새 메모 등록 화면 링크 제공
- [x] 권장: 등록된 메모가 없을 때 안내 문구 표시

### 메모 상세 조회

- [x] `GET /memos/{memo_id}` 구현
- [x] 저장소에 ID 기반 단건 조회 기능 작성
- [x] 서비스를 통해 메모 단건 조회
- [x] 상세 화면에 메모 전체 필드 표시
- [x] 수정 화면으로 이동하는 링크 또는 버튼 제공
- [x] 삭제 버튼 제공
- [x] 목록으로 돌아가는 링크 제공
- [x] 존재하지 않는 메모 조회 시 안내 화면 또는 목록 리다이렉트 적용

### 메모 등록

- [x] `GET /memos/new` 등록 화면 구현
- [x] 제목 및 내용 입력 필드 작성
- [x] 저장 버튼과 목록 화면으로 돌아가는 취소 링크 작성
- [x] 등록 폼의 전송 방식을 POST로 지정
- [x] FastAPI `Form()`으로 입력값 수신
- [x] 서비스에 메모 등록 로직 작성
- [x] 저장소에 ORM 기반 INSERT 기능 작성
- [x] 등록 완료 후 `RedirectResponse` 사용
- [x] 등록 리다이렉트에 `status_code=303` 적용
- [x] 새로고침 시 중복 등록이 발생하지 않는지 확인

### 메모 수정

- [x] `GET /memos/{memo_id}/edit` 수정 화면 구현
- [x] 수정 폼에 기존 메모 값 표시
- [x] 저장 버튼과 목록 화면으로 돌아가는 취소 링크 작성
- [x] 수정 폼의 전송 방식을 POST로 지정
- [x] FastAPI `Form()`으로 수정값 수신
- [x] 서비스에 메모 수정 로직 작성
- [x] 저장소에 ORM 기반 UPDATE 기능 작성
- [x] 수정 완료 후 `RedirectResponse` 사용
- [x] 수정 리다이렉트에 `status_code=303` 적용
- [x] 권장: 존재하지 않는 메모 수정 요청 처리

### 메모 삭제

- [x] `POST /memos/{memo_id}/delete` 구현
- [x] 상세 화면에 삭제 버튼 작성
- [x] 삭제 요청을 POST 방식으로 처리
- [x] 서비스에 메모 삭제 로직 작성
- [x] 저장소에 ORM 기반 DELETE 기능 작성
- [x] 삭제 완료 후 목록 화면으로 HTTP 303 리다이렉트
- [x] 권장: 존재하지 않는 메모 삭제 요청 처리

### SSR 및 템플릿

- [x] 선택 사항: 공통 레이아웃 템플릿 작성
- [x] 홈, 목록, 상세, 등록, 수정 템플릿 작성
- [x] 존재하지 않는 데이터 조회 시 안내 화면을 표시하거나 목록으로 리다이렉트
- [x] 모든 주요 GET 화면에서 `TemplateResponse` 사용
- [x] 템플릿에 `request` 객체 전달
- [x] 화면 사이를 이동할 수 있는 링크 구성

### 레이어 분리

- [x] 라우터는 요청 데이터 수신과 응답 생성만 담당
- [x] 라우터에서 SQLAlchemy 조회문 직접 작성 금지
- [x] 서비스에 비즈니스 로직 작성
- [x] 저장소에 데이터 접근 로직 작성
- [x] 저장소에서 SQLAlchemy `Session` 사용
- [x] 모델에 SQLAlchemy ORM 테이블 정의
- [x] FastAPI `Depends`로 DB 세션 전달
- [x] 권장: SQLAlchemy ORM 모델을 직접 노출하지 않고 Pydantic Schema 또는 DTO로 분리

### PRG 패턴

- [x] 등록·수정·삭제 요청을 POST로 처리
- [x] 각 POST 처리 이후 GET 화면으로 리다이렉트
- [x] 모든 POST 리다이렉트에 HTTP 303 적용
- [x] 리다이렉트 후 새로고침 테스트
- [x] 새로고침으로 데이터가 중복 처리되지 않는지 확인

## 보너스 과제

### 메모 검색 기능

- [x] 목록 화면에 검색 입력 필드 추가
- [x] 검색 폼을 GET 방식으로 처리
- [x] 쿼리 파라미터로 검색어 수신
- [x] 제목에 검색어가 포함된 메모 조회
- [x] SQLAlchemy `filter()` 또는 `like()` 사용
- [x] 검색 결과가 없을 때 안내 문구 표시
- [x] 검색어를 비우면 전체 목록 표시

### 서버 사이드 검증

- [x] 제목 및 내용 필수값 검증
- [x] 공백만 입력한 값이 저장되지 않도록 처리
- [x] 검증 로직을 서비스 계층에 작성
- [x] 검증 실패 시 폼 화면과 안내 문구 표시
- [x] 기존 입력값이 폼에서 유지되도록 처리
- [x] 잘못된 데이터가 DB에 저장되지 않는지 확인

### 수정 및 삭제 UX 개선

- [x] 상세 화면에서 수정 화면으로 자연스럽게 이동
- [x] 상세 화면에 삭제 버튼 배치
- [x] 삭제 전 확인 메시지 제공
- [x] 작업 완료 후 적절한 화면으로 이동
- [x] 목록·상세·등록·수정 화면 사이의 이동 경로 구성

## 제약 사항

- Python 3.10 이상 사용
- FastAPI, Uvicorn, SQLAlchemy, Jinja2, python-multipart 사용
- 지정된 필수 패키지 외 외부 라이브러리 추가 금지
- 서버 메모리 리스트 또는 딕셔너리만으로 데이터 관리 금지
- SQLite 데이터베이스에 데이터 저장
- 라우터, 서비스, 저장소, 모델 역할 분리
- 등록 및 수정 폼에 POST 방식 사용
- 폼 데이터는 FastAPI `Form()`으로 수신
- 등록·수정·삭제 이후 HTTP 303 리다이렉트 적용
- DB 세션은 FastAPI `Depends`로 관리
- 로그인, 인증 및 권한 기능 구현 금지
- 모델 간 연관관계 구현 금지
- 단일 모델의 CRUD 범위 유지
- 주요 화면은 Jinja2 `TemplateResponse`로 출력
