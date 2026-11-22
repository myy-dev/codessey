# 로그인이 되고 회원끼리 연결되는 웹 서비스 만들기

## 프로젝트 개요

FastAPI와 SQLAlchemy를 사용해 사용자 인증·인가, 모델 연관관계와 할 일 상태 변경 기능을 갖춘 웹 서비스를 구현하는 프로젝트

## 기술 스택

| 구분 | 기술 |
| --- | --- |
| 언어 | Python 3.10 이상 |
| 프레임워크 | FastAPI 0.116.1 |
| ASGI 서버 | Uvicorn 0.35.0 |
| ORM | SQLAlchemy 2.0.41 |
| 데이터베이스 | SQLite |

전체 의존성과 버전은 [requirements.txt](requirements.txt) 참고

## 프로젝트 구조

```text
B6-3/
├── main.py             # 앱 초기화, 미들웨어, 전역 예외 처리
├── core/               # 설정, DB, 공통 예외와 화면 도구
├── auth/               # 인증·인가, CSRF, OAuth
├── routers/            # 요청·응답 처리
├── services/           # 입력 검증, 소유권, 상태 변경 규칙
├── repositories/       # 데이터 조회·변경
├── models/             # User, Project, Task ORM 모델
├── templates/          # Jinja2 SSR 화면
├── static/             # 반응형 스타일
├── tests/              # 도메인·저장소·HTTP 검사
├── docs/               # 구조, ERD, 인증, 경로, 배포 문서
├── requirements.txt    # 의존성과 버전
├── .env.example        # 환경 변수 예시
├── render.yaml         # Render 배포 설정
└── Procfile            # 배포 서버 실행 명령
```

## 배포 주소

<https://b6-3.onrender.com/>

## 로컬 실행

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
# http://127.0.0.1:8000 접속
```

## 테스트 계정과 인증

| 항목 | 내용 |
| --- | --- |
| 테스트 계정 | ID `demo` / PW `demo1234` |
| 저장 방식 | DB 저장, 서버 시작 시 계정이 없으면 생성 |
| 인증 방식 | 서명된 세션 쿠키의 `user_id`로 사용자 조회 |
| 선택 이유 | 브라우저 기반 SSR에 적합한 쿠키를 통한 로그인 상태 전달 |

## 공개·보호 경로 정책

| HTTP | 경로 | 접근 정책 |
| --- | --- | --- |
| `GET` | `/`, `/health`, `/docs`, `/redoc`, `/openapi.json`, `/static/*` | 공개 |
| `GET`, `POST` | `/login`, `/signup` | 공개 |
| `GET` | `/auth/github`, `/auth/github/callback` | 공개 |
| `POST` | `/logout` | 로그인 필수 |
| `GET`, `POST` | 등록된 `/app/` 기능 경로 | 로그인 필수, 본인 소유 데이터만 접근 |

보호 라우터의 `CurrentUser` 의존성을 통한 인증 검사와 비로그인 요청의 로그인 화면 이동

## 주요 기능 경로

| 기능 | HTTP | 경로 |
| --- | --- | --- |
| 프로젝트 목록·검색 | `GET` | `/app/projects?q=검색어` |
| 프로젝트 생성 | `POST` | `/app/projects` |
| 프로젝트 상세·할 일 검색·필터 | `GET` | `/app/projects/{project_id}?q=검색어&status=completed` |
| 할 일 생성 | `POST` | `/app/projects/{project_id}/tasks` |
| 할 일 상태 변경 | `POST` | `/app/tasks/{task_id}/status` |
| 할 일 삭제 | `POST` | `/app/tasks/{task_id}/delete` |
| 프로젝트와 자식 할 일 삭제 | `POST` | `/app/projects/{project_id}/delete` |

## 수행 항목 체크리스트

- [x] Python 가상환경, 패키지 버전, 실행 방법 명시
- [x] 인증·요청·서비스·저장소·모델·화면 계층 분리
- [x] `Depends` 기반 인증, 로그인·로그아웃, 성공·실패 안내
- [x] 로그인 여부에 따른 상단 메뉴 변경과 보호 경로 접근 제어
- [x] 프로젝트와 할 일의 사용자별 소유권 검사
- [x] `User → Project → Task` 모델 3개와 양방향 1:N 관계 2개 구성, N:M 미사용
- [x] 프로젝트 목록의 할 일 수와 상세 화면의 연관 할 일 목록 표시
- [x] 부모 삭제 시 자식 연쇄 삭제, 선택 이유를 모델 코드 주석에 명시
- [x] SQLAlchemy ORM·SQLite 저장과 요청별 DB 세션 정리
- [x] 대기·진행 중·완료 사이 상태 변경, 잘못된 값·동일 상태 변경 차단
- [x] 알림과 카드 표시로 상태 변경 결과 확인
- [x] Jinja2 SSR·반응형 화면, 변경 성공 후 HTTP 303 이동

## 보너스 과제

- [x] 전역 예외 처리와 공통 오류 화면
- [x] 프로젝트·할 일 검색과 상태 필터
- [x] GitHub OAuth2 로그인과 실제 계정 세션 유지 확인
- [x] 회원가입, 입력값·아이디 중복 검사, PBKDF2-SHA256 비밀번호 해싱
- [x] Render 배포와 외부 접속 URL 제출

추가 라이브러리 없이 표준 라이브러리 `urllib`로 OAuth HTTP 통신 구현

## 결과물

- [테스트 계정과 인증 방식](docs/authentication.md)
- [경로와 접근 정책](docs/routes.md)
- [서비스 구조와 동작](docs/architecture.md)
- [환경 변수와 배포](docs/deployment.md)
