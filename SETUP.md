# 설치 및 실행 방법

## 준비

Python 3.10 이상, Git, OpenAI API 키가 필요하다. 모의 테스트와 전송 미리보기는 키 없이
실행할 수 있다. 별도의 웹 화면이나 GitHub 토큰은 필요하지 않다.

```bash
git clone https://github.com/myy-dev/B3-2.git
cd B3-2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell에서는 `python -m venv .venv`로 만들고
`.venv\Scripts\Activate.ps1`로 활성화한다. 이후 명령은 동일하다.

## API 키 설정

키 발급처: [OpenAI Platform](https://platform.openai.com/api-keys).
프로젝트 루트의 `.env.example`을 `.env.local`로 복사한다. 이미 키를 저장한 파일은
덮어쓰지 않는다. 텍스트 편집기에서 다음 한 줄의 `=` 뒤에 본인 키를 입력하고 저장한다.

```dotenv
AI_API_KEY=본인의_OpenAI_API_키
```

`.env.local`은 Git에서 제외한다. macOS/Linux에서는 `chmod 600 .env.local`로 소유자만
읽고 쓸 수 있게 한다. 키를 코드·문서·로그·채팅에 붙이지 않는다. 프로그램은 루트의
`.env.local`만 읽으며 파일의 명령이나 변수 치환을 실행하지 않는다.

파일을 사용하지 않으려면 실행할 셸의 `AI_API_KEY` 환경변수로 설정한다.
환경변수가 `.env.local`보다 우선하며, `OPENAI_API_KEY`는 이 프로젝트에서 사용하지 않는다.

## 기본 실행

항상 변경을 설명할 Git 프로젝트 **루트**에서 실행한다. 기본 범위는 staged + unstaged +
untracked이고, 무시된 파일은 수집하지 않는다.

```bash
python main.py commit
python main.py pr
python main.py commit --model gpt-4.1-mini --temperature 0.2 --max-tokens 1200 --safe-mode
```

설명할 저장소가 다른 디렉터리라면 그 저장소의 루트로 이동한 다음 설치한 `main.py`의
절대 경로로 실행할 수 있다. 환경 설정과 Git 수집은 현재 저장소 루트를 기준으로 한다.

```bash
python main.py commit --staged
python main.py pr --base main
python main.py pr --json
python main.py commit --convention none
```

`--base main`은 `main`과 HEAD의 공통 조상 이후 커밋 변경에 현재 작업 변경을 더한다.
기본 동작은 아직 커밋하지 않은 변경만 포함한다. `--staged`와 `--base`는 동시에 쓸 수 없다.

## 전송 내용 확인과 결과 적용

```bash
# 실제 요청 메시지 확인, 키 불필요, API 0회
python main.py pr --safe-mode --preview
```

기본 안전 모드는 마스킹과 10파일/200줄/20,000자 제한을 적용한다. 전체·전송·제외·생략
파일 수와 잘림 안내를 확인한다. 자세한 정책과 ON/OFF 비교는 [안전 정책](docs/SAFETY.md)에 있다.

생성 결과는 요약, 제목, 본문으로 구분한다. commit/pr 명령마다 API 요청 횟수를 출력한다.
커밋 제목은 최대 72자, PR 제목은 최대 80자이고 초과하면 로컬에서 보정한다.
PR의 `Why`, `What`, `How to Test` 섹션은 각각 불릿을 포함한다.

사용자는 누락된 맥락과 변경 유형을 검토하고, 제안한 테스트를 실제로 실행한 뒤 내용을
수정하여 복사한다. 이 CLI는 커밋, push, GitHub PR 생성 또는 테스트 실행을 하지 않는다.

## 오류 처리

| 상황 | 결과와 해결 |
| --- | --- |
| 변경 없음 | 안내 후 정상 종료, API 0회 |
| Git 없음/저장소 아님/명령 실패 | 명령과 원인 표시, Git 설치 또는 경로 확인 |
| 저장소 하위 폴더 | 프로젝트 루트 안내 |
| 키 없음 | `AI_API_KEY` 또는 `.env.local` 설정 안내 |
| HTTP 401/403 | 키 유효성·프로젝트/모델 권한 확인 |
| HTTP 400/404 | 모델 이름과 지원하는 옵션 확인 |
| HTTP 429 | 크레딧·결제·요청 한도 확인 |
| 네트워크/시간초과 | 인터넷·DNS·프록시·TLS 확인, 자동 재시도 없음 |
| 토큰 한도로 응답 잘림 | `--max-tokens`를 늘려 직접 재실행 |
| 잘못된 JSON/모델 거절 | 실패 안내, 응답 원문 및 키 출력 없음 |

종료 코드: 성공/변경 없음 `0`, Git·API·설정 오류 `1`, 잘못된 CLI 인자/의존성 누락 `2`,
사용자 중단 `130`. `--json` 오류는 stdout의 JSON, 일반 오류는 stderr에 출력한다.

## 테스트 및 시연 기록

```bash
python -m pip install -r requirements-dev.txt
python -m pytest --cov=ai_gitgen --cov=main --cov-report=term-missing -q
ruff check .
ruff format --check .
python -m pip check
python -m scripts.demo_safety
```

- 로컬 검증과 범위: [검증 기록](docs/VERIFICATION.md)
- 팀 컨벤션 및 이력 분석: [컨벤션](docs/CONVENTION.md)
- 합성 데이터 안전 모드 비교: [비교 결과](docs/examples/safety-comparison.json)
- 게시 전 검토 자료: [PR 초안](docs/PR_DRAFT.md)
- 실제 OpenAI 생성 3회 성공 및 컨벤션별 비교: [실행 기록](docs/examples/live-run.json)
- AI 초안 대비 최종 PR 수정 8줄: [수정 내역](docs/PR_CHANGES.md)
- 실제 PR 링크: [myy-dev/B3-2 #1](https://github.com/myy-dev/B3-2/pull/1)

모의 테스트와 실제 OpenAI 생성 결과를 구분하여 기록했다. 실제 PR의 게시된 본문에서
Why/What/How to Test 섹션과 각각 2/6/7개의 불릿을 확인했다.
