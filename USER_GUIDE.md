# 사용 가이드

이 문서는 Git 변경 사항을 OpenAI API에 전달해 커밋 메시지와 Pull Request 초안을
생성하는 터미널 도구의 설치와 사용 방법을 설명한다.

프로젝트 시연 순서는 [SETUP.md](SETUP.md)를 확인한다.

## 요구사항

- Python 3.10 이상
- Git
- OpenAI API Key
- Git이 초기화된 프로젝트의 루트 디렉터리

## 설치

### 1. 저장소 복제 및 이동

```bash
git clone https://github.com/myy-dev/B3-2.git
cd B3-2
```

### 2. 가상환경 생성 및 활성화

가상환경은 필수는 아니지만 프로젝트별 의존성 충돌을 막기 위해 권장한다.

macOS 또는 Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. 의존성 설치

```bash
python -m pip install -r requirements.txt
```

## API Key 설정

프로젝트 루트의 `.env` 파일 또는 셸 환경변수에 `AI_API_KEY`를 설정한다. 셸 환경변수가
있으면 `.env`보다 우선한다.

`.env` 파일:

```dotenv
AI_API_KEY=YOUR_OPENAI_API_KEY
```

macOS 또는 Linux:

```bash
export AI_API_KEY="YOUR_OPENAI_API_KEY"
```

Windows PowerShell:

```powershell
$env:AI_API_KEY="YOUR_OPENAI_API_KEY"
```

API Key를 소스 코드, 로그, 문서 또는 Git 이력에 기록하지 않는다. `.env`는 Git에서
제외되도록 설정되어 있다.

## 기본 사용법

명령은 Git 프로젝트 루트에서 실행한다.

### 커밋 메시지 생성

```bash
python main.py commit --safe-mode
```

### Pull Request 초안 생성

```bash
python main.py pr --safe-mode
```

각 명령은 Git의 staged, unstaged, untracked 변경 사항을 수집해 OpenAI API를 한 번
호출한다. 변경 사항이 없으면 API 호출 없이 안내 메시지를 출력하고 종료한다.

## CLI 옵션

옵션은 `commit` 또는 `pr` 뒤에 작성한다.

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--model` | `gpt-4.1-mini` | 사용할 OpenAI 모델 |
| `--temperature` | `0.2` | 생성 다양성, `0`~`2` |
| `--max-tokens` | `1200` | 최대 출력 토큰, `64`~`32768` |
| `--safe-mode` | ON | 민감정보 마스킹 및 전송량 제한 |
| `--no-safe-mode` | OFF | 안전 모드 전용 마스킹·전송량 제한 해제 |
| `--convention` | `team` | `team` 또는 `none` 컨벤션 적용 |

예시:

```bash
python main.py commit --model gpt-4.1-mini --temperature 0.2 --max-tokens 1200
python main.py pr --convention none
```

## 출력과 생성 규칙

### 커밋 메시지

- 변경 요약과 커밋 제목을 출력한다.
- 제목은 한 줄이며 최대 72자다. 50자 이내를 권장한다.
- 본문이 생성되면 핵심 변경을 1~2개 불릿으로 출력한다.

### Pull Request 초안

- PR 제목과 본문을 구분해 출력한다.
- 본문에 `Why`, `What`, `How to Test` 섹션을 포함한다.
- 각 섹션에는 하나 이상의 불릿을 포함한다.
- `How to Test`의 항목은 실제 실행 여부를 혼동하지 않도록 `미실행:`으로 표시한다.

모든 결과에는 변경 요약, 구분선, API 요청 횟수와 최종 검토 안내가 포함된다. 생성된
문구는 검토·수정한 뒤 직접 커밋이나 PR에 적용한다. 프로그램은 커밋, `git push`,
GitHub PR 게시를 실행하지 않는다.

## 안전 모드

안전 모드는 기본으로 켜져 있다.

- API Key, 이메일, 비밀번호, 개인키 등의 패턴을 `[REDACTED]`로 마스킹한다.
- 최대 10개 파일, 200줄, 20,000자까지만 변경 내용을 전송한다.
- `.env`, 자격증명 파일, 개인키 파일, 심볼릭 링크는 두 모드에서 모두 제외한다.
- `--no-safe-mode`는 안전 모드 전용 패턴 마스킹과 전송량 상한을 해제한다.
- 실행 전 변경 파일에 패턴으로 탐지되지 않는 민감정보가 없는지 확인한다.

안전 모드 비교는 [SETUP.md](SETUP.md)의 시연 시나리오를 따른다. 실제 자격증명을
사용하지 않는 비교 명령은 다음과 같다.

```bash
python -m scripts.demo_safety
```

## 오류와 해결

| 메시지 또는 상황 | 해결 방법 |
| --- | --- |
| Git 프로젝트 루트가 아님 | Git이 초기화된 프로젝트 루트에서 다시 실행 |
| `AI_API_KEY`가 없음 | 셸 환경변수 또는 루트 `.env`에 키 설정 |
| 변경 사항이 없음 | 파일을 수정하거나 staged 변경을 만든 뒤 실행 |
| API 인증 실패 | OpenAI API Key와 사용 권한 확인 |
| 네트워크 연결 실패 | 인터넷, DNS, 프록시와 TLS 설정 확인 |
| 모델을 찾을 수 없음 | `--model` 값과 모델 사용 권한 확인 |
| 요청 한도·크레딧 부족 | OpenAI 사용량·결제 상태와 호출 횟수 확인 |
| 출력이 길이 제한으로 잘림 | `--max-tokens`를 늘려 직접 다시 실행 |

오류가 발생해도 프로그램은 API 응답 본문이나 민감정보를 그대로 출력하지 않으며,
실제 API 요청 횟수를 함께 표시한다.

## 개발자 검증

실제 OpenAI API를 호출하지 않는 자동 테스트:

```bash
python -m pytest -q
```

프로젝트 시연 결과와 실제 생성 기록은 [SETUP.md](SETUP.md)의 증빙 링크에서 확인한다.
