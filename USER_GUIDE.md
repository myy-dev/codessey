# 사용자 가이드

Git 변경 사항을 OpenAI API에 전달해 커밋 메시지와 Pull Request 초안을 생성하는
터미널 도구의 설치 및 사용 방법

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

macOS 또는 Linux 환경

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell 환경

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. 의존성 설치

```bash
python -m pip install -r requirements.txt
```

## API Key 설정

프로젝트 루트의 `.env` 파일 또는 셸 환경변수에 `AI_API_KEY` 설정
셸 환경변수 존재 시 `.env`보다 우선

`.env` 파일 설정 예시

```dotenv
AI_API_KEY=YOUR_OPENAI_API_KEY
```

macOS 또는 Linux 환경

```bash
export AI_API_KEY="YOUR_OPENAI_API_KEY"
```

Windows PowerShell 환경

```powershell
$env:AI_API_KEY="YOUR_OPENAI_API_KEY"
```

## 기본 사용법

### 커밋 메시지 생성

```bash
python main.py commit --safe-mode
```

### Pull Request 초안 생성

```bash
python main.py pr --safe-mode
```

## CLI 옵션

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--model` | `gpt-4.1-mini` | 사용할 OpenAI 모델 |
| `--temperature` | `0.2` | 생성 다양성, `0`~`2` |
| `--max-tokens` | `1200` | 최대 출력 토큰, `64`~`32768` |
| `--safe-mode` | ON | 민감정보 마스킹 및 전송량 제한 적용 |
| `--no-safe-mode` | OFF | 안전 모드 비활성화 명시 |
| `--convention` | `team` | `team` 또는 `none` 컨벤션 적용 |

사용 예시

```bash
python main.py commit --model gpt-4.1-mini --temperature 0.2 --max-tokens 1200
python main.py pr --convention none
```

## 출력과 생성 규칙

### 커밋 메시지

- 변경 요약 및 커밋 제목 출력
- 한 줄 제목, 최대 72자, 권장 길이 50자 이내
- 본문 생성 시 핵심 변경 1~2개 불릿 출력

### Pull Request 초안

- PR 제목 및 본문 구분 출력
- 본문에 `Why`, `What`, `How to Test` 섹션 포함
- 섹션별 하나 이상의 불릿 포함

## 안전 모드

- API Key, 이메일, 비밀번호, 개인키 등의 패턴을 `[REDACTED]`로 마스킹
- 최대 10개 파일·200줄·20,000자의 변경 내용 전송 상한
- 두 모드 공통 제외 대상은 `.env`, 자격증명 파일, 개인키 파일, 심볼릭 링크
- `--no-safe-mode`에서 안전 모드 전용 패턴 마스킹 및 전송량 상한 해제
- 실행 전 패턴으로 탐지되지 않는 민감정보 포함 여부 확인

## 오류와 해결

오류 발생 시 API 응답 본문 및 민감정보 미출력, 실제 API 요청 횟수 표시

| 메시지 또는 상황 | 해결 방법 |
| --- | --- |
| Git 프로젝트 루트가 아님 | Git이 초기화된 프로젝트 루트에서 다시 실행 |
| `AI_API_KEY`가 없음 | 셸 환경변수 또는 루트 `.env`에 키 설정 |
| 변경 사항이 없음 | 파일을 수정하거나 변경 사항을 만든 뒤 실행 |
| API 인증 실패 | OpenAI API Key와 사용 권한 확인 |
| 네트워크 연결 실패 | 인터넷, DNS, 프록시와 TLS 설정 확인 |
| 모델을 찾을 수 없음 | `--model` 값과 모델 사용 권한 확인 |
| 요청 한도·크레딧 부족 | OpenAI 사용량·결제 상태와 호출 횟수 확인 |
| 출력이 길이 제한으로 잘림 | `--max-tokens`를 늘려 직접 다시 실행 |
