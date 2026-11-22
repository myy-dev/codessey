# 경로와 접근 정책

## 공개·보호 경로 정책

| HTTP | 경로 | 정책 | 설명 |
| --- | --- | --- | --- |
| `GET` | `/` | 공개 | 로그인 상태에 따라 상단 메뉴가 달라지는 홈 |
| `GET`, `POST` | `/login`, `/signup` | 공개 | 로그인·회원가입 화면과 처리 |
| `GET` | `/auth/github` | 공개 | GitHub OAuth 인증 시작 |
| `GET` | `/auth/github/callback` | 공개 | OAuth state 검증과 로그인 완료 |
| `GET` | `/health` | 공개 | 서버 상태 확인 |
| `GET` | `/docs`, `/redoc`, `/openapi.json` | 공개 | FastAPI 자동 API 문서 |
| `GET` | `/static/*` | 공개 | 스타일시트 등 정적 파일 |
| `POST` | `/logout` | 보호 | 세션 초기화와 로그아웃 |
| `GET`, `POST` | 등록된 `/app/` 기능 경로 | 보호 | 프로젝트·할 일 기능 |

- 보호 라우터의 `CurrentUser` 의존성을 통한 비로그인 요청의 로그인 화면 이동
- 다른 사용자 소유의 프로젝트·할 일 접근 차단과 변경 폼의 CSRF 토큰 검증

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

- 검색·상태 쿼리 생략 가능
- 상태 값으로 `todo`·`in_progress`·`completed` 사용
- 상태 변경 POST의 폼 필드로 `new_status` 사용
