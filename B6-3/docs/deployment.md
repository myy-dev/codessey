# 환경 변수와 배포

## 환경 변수

- 프로세스 환경 변수 사용과 `.env` 파일 자동 로드 미지원
- [.env.example](../.env.example)을 참고해 로컬 셸 또는 Render의 **Environment**에 등록

| 변수 | 용도 | 로컬 기본값 | Render 설정 |
| --- | --- | --- | --- |
| `APP_SECRET_KEY` | 세션 쿠키 서명 | 개발용 기본값 | 긴 무작위 값, 배포 간 유지 |
| `DATABASE_URL` | DB 연결 URL | `sqlite:///./database.db` | 로컬 기본값과 동일 |
| `SESSION_HTTPS_ONLY` | HTTPS 전용 세션 쿠키 | `false` | `true` |
| `GITHUB_CLIENT_ID` | GitHub OAuth Client ID | 미설정 | 발급받은 값 |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth 비밀값 | 미설정 | 발급받은 값 |

- 세션 쿠키 서명용 비밀키 생성 후 Render의 `APP_SECRET_KEY`에 등록

```sh
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## GitHub 소셜 로그인 설정

1. GitHub **Settings → Developer settings → OAuth Apps**에서 앱 생성 또는 기존 앱 선택
2. 아래 주소 등록과 Client ID·Client secret 확인·발급
3. Render Environment에 두 값 등록 후 재배포

| 항목 | 배포용 값 |
| --- | --- |
| Application name | `FlowTask` |
| Homepage URL | `https://b6-3.onrender.com` |
| Authorization callback URL | `https://b6-3.onrender.com/auth/github/callback` |

- 로컬용 별도 OAuth App의 콜백은 `http://127.0.0.1:8000/auth/github/callback`으로 설정
- 서버 포트 변경 시 콜백 포트도 동일하게 변경

```sh
export GITHUB_CLIENT_ID='...'
export GITHUB_CLIENT_SECRET='...'
uvicorn main:app --reload
```

## Render 배포

`myy-dev/B5-3` 저장소의 `main` 브랜치와 `.python-version` 사용

- **Blueprint:** 코드와 [render.yaml](../render.yaml) 반영 후 **New → Blueprint**에서 저장소 연결, `APP_SECRET_KEY` 자동 생성과 OAuth 변수 별도 등록
- **직접 생성:** **New → Web Service**에서 저장소 연결 후 아래 설정과 환경 변수 표 적용

| 항목 | 설정 |
| --- | --- |
| Language / Instance Type | Python 3 / Free |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |

- Render에서 `PORT` 제공
- 배포 후 [공개 주소](https://b6-3.onrender.com/)와 [/health](https://b6-3.onrender.com/health) 응답 확인
- 데모 로그인·로그아웃과 GitHub 로그인·새로고침 후 세션 유지 확인

## 데이터 저장과 접속

- 영구 디스크·외부 DB 없이 SQLite를 사용하는 과제 시연용 구성
- 재시작·재배포·절전 시 파일 변경 소실과 다음 시작 시 테이블·데모 계정 재생성
- 무료 서비스의 15분 무요청 시 절전 전환과 다음 접속 시 기동 시간 소요
