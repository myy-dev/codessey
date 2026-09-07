# 내가 고친 코드 설명을 AI가 대신 써주는 도우미 만들기

## 프로젝트 개요 (Project Overview)

- Git 변경 사항 수집 및 AI API 전달, 변경 맥락 기반 커밋 메시지와 Pull Request 제목·본문 초안 생성 Python CLI 도구

## 실행 환경 (Environment)

- **언어**: Python 3.10 이상
- **외부 API**: OpenAI API
- **환경변수**: `AI_API_KEY`

## 프로젝트 구조 (Project Structure)

```text
.
├── main.py               # CLI, 환경 설정, 출력
├── ai_gitgen/            # Git 수집, API 호출, 검증, 안전 정책
├── tests/                # 임시 Git 저장소 및 모의 API 자동 테스트
├── scripts/              # API 없이 재현하는 안전 모드 시연
├── docs/                 # 검증 기록, 컨벤션, 안전 정책, PR 검토 초안
├── requirements.txt      # 실행 의존성
├── requirements-dev.txt  # 테스트·린트 의존성
├── .env.example          # 빈 키 설정 예시
├── README.md             # 프로젝트 개요 및 개발 체크리스트
└── SETUP.md              # 설치·실행 방법 및 프로젝트 시현
```

## 빠른 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
# .env.example을 .env.local로 복사하고 AI_API_KEY에 본인 키 입력
python main.py commit --safe-mode
python main.py pr --safe-mode
# 키와 API 호출 없이 전송 컨텍스트 확인
python main.py pr --preview
```

설치와 Windows 안내는 [SETUP.md](SETUP.md), 안전 정책은 [docs/SAFETY.md](docs/SAFETY.md),
컨벤션은 [docs/CONVENTION.md](docs/CONVENTION.md)를 참고한다.

## 수행 항목 체크리스트

`[x]`는 구현과 로컬 자동 테스트로 검증한 항목이다. 실제 OpenAI 초안 생성도
커밋 컨벤션 전·후와 PR에 각각 1회씩 총 3회 성공했다. 요청별 제목·본문 규칙과
입력 동일성을 검증했다. 사용자 검토 후 [실제 PR #1](https://github.com/myy-dev/B3-2/pull/1)을 게시했고,
AI 초안 대비 수정 내역 8줄과 게시된 본문의 섹션·불릿도 확인했다.
자세한 근거는 [docs/VERIFICATION.md](docs/VERIFICATION.md)에 기록한다.

### Git 변경 사항 수집

- [x] Git이 초기화된 프로젝트 루트에서 CLI 실행
- [x] `git status` 결과를 수집해 변경된 파일 목록 확인
- [x] `git diff` 결과를 수집해 변경 내용 확보
- [x] 변경 사항이 없으면 안내 메시지 출력 후 종료
- [x] Git 명령 실행 실패 시 원인을 포함한 오류 메시지 출력

### AI API 연동

- [x] API Key를 `AI_API_KEY` 환경변수로 관리하고 코드에 하드코딩하지 않기
- [x] Git 변경 사항을 컨텍스트로 포함해 AI API 호출
- [x] 생성된 커밋 메시지 또는 PR 초안을 터미널에 출력
- [x] 변경 요약을 커밋 메시지 또는 PR 초안과 함께 출력
- [x] 네트워크 오류, 인증 실패 등 API 오류 원인 안내
- [x] `--model`, `--temperature`, `--max-tokens` CLI 옵션 및 기본값 제공
- [x] `commit`, `pr` 명령별 API 요청을 1회로 제한하고 호출 횟수 출력(권장)

### 커밋 메시지 자동 생성

- [x] `commit` 명령으로 커밋 메시지 생성
- [x] 변경 사항 요약을 기반으로 커밋 제목 1줄 출력
- [x] 커밋 제목은 50자 이내 권장, 최대 72자로 제한
- [x] 커밋 본문 사용 시 변경 파일 1~3개 또는 핵심 변경 사항 1~2개를 불릿으로 요약
- [x] 생성 결과를 사용자가 복사할 수 있도록 명확한 구획으로 출력

### Pull Request 제목·본문 자동 생성

- [x] `pr` 명령으로 PR 제목과 본문 초안 생성
- [x] PR 제목을 1줄, 최대 80자로 제한
- [x] PR 본문에 `Why`, `What`, `How to Test` 섹션 포함
- [x] 각 PR 본문 섹션에 최소 1개 이상의 불릿 포함
- [x] PR 제목과 본문을 구분해 터미널에 출력

### 출력 형식 검증 및 다듬기

- [x] 커밋 제목 길이 규칙 검증
- [x] PR 제목 길이 규칙 검증
- [x] PR 필수 섹션과 섹션별 불릿 존재 여부 검증
- [x] 규칙 위반 시 재생성 또는 후처리 수행
- [x] 최종 출력에 헤더와 구분선을 적용해 가독성 확보

### 보안 및 안전 모드

- [x] `--safe-mode` 옵션 제공
- [x] 다음 안전 정책 중 1개 이상 구현
  - [x] API Key, 이메일 등 민감정보 패턴을 마스킹한 뒤 전송
  - [x] 전송 가능한 diff의 파일 수 또는 줄 수 제한
- [x] 생성 결과를 사용자가 반드시 검토한 뒤 적용하도록 안내

### 보너스 과제

- [x] 기존 프로젝트에 의미 있는 변경을 적용하고 실제 PR 1건 완성
- [x] AI 초안과 최종 PR의 변경점을 5~10줄로 정리
- [x] 기존 커밋/PR 스타일을 분석해 팀 컨벤션 정의
- [x] `.ai-gitgen.yml`, `--convention`, 프롬프트 템플릿 중 하나로 컨벤션 적용
- [x] 컨벤션 적용 전·후 생성 결과 비교
- [x] 정규표현식 기반 마스킹 또는 diff 전송 제한 정책 고도화
- [x] 안전 모드 ON/OFF 결과 비교

### 제약 사항 (Constraints)

- **API Key 관리**: 환경변수 전용 관리, 소스 코드·로그·Git 이력 미포함
- **AI API 요청**: 과도한 비용 방지를 위한 1회 실행당 1~2회 이내 제한
- **Git 연동 범위**: `git status`, `git diff` 기반 변경 사항 수집
- **자동화 범위**: 커밋 메시지 및 PR 초안 출력
- **원격 작업 금지**: `git push` 및 GitHub PR 생성 API 자동 실행 금지
- **사용자 검토**: AI 생성 결과 검토·수정 후 적용
- **실행 인터페이스**: 별도 웹 화면 없이 터미널 실행

### 커스텀 설정값 명세

| 항목 | 기준값 | 비고 |
| --- | --- | --- |
| Python 버전 | 3.10 이상 | 필수 |
| 1회 실행당 API 요청 | 1~2회 이내 | 비용 방지 권장값 |
| 커밋 제목 | 50자 이내 권장, 최대 72자 | 검증 후 재생성 또는 후처리 |
| PR 제목 | 최대 80자 | 초과 불가 |
| PR 본문 | 필수 섹션 3개 | `Why`, `What`, `How to Test` |
| PR 섹션별 내용 | 불릿 1개 이상 | 각 섹션 공통 |
| 안전 모드 파일 제한 | 최대 10개 | 구현 시 변경 가능 |
| 안전 모드 diff 제한 | 최대 200줄 | 구현 시 변경 가능 |

### CLI 옵션

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--model` | `gpt-4.1-mini` | Chat Completions + JSON schema를 지원하는 모델 |
| `--temperature` | `0.2` | 0~2 범위의 생성 다양성 |
| `--max-tokens` | `1200` | 64~32768, API의 `max_completion_tokens`로 전달 |
| `--safe-mode` | ON | 마스킹 및 최대 10파일/200줄/20,000자 제한 |
| `--no-safe-mode` | OFF | 패턴 마스킹·안전 모드 전용 상한 해제 |
| `--convention` | `team` | `team` 또는 `none` |
| `--staged` | OFF | 스테이징된 변경만 수집 |
| `--base REF` | 없음 | 공통 조상 이후 커밋 변경도 포함, `--staged`와 동시 사용 불가 |
| `--preview` | OFF | 전송할 메시지만 출력, API 요청 0회 |
| `--json` | OFF | 초안·요약·메타데이터를 JSON으로 출력 |

### OpenAI 연결 명세

- 공급자: OpenAI, 엔드포인트: `POST https://api.openai.com/v1/chat/completions`
- 기본 모델: `gpt-4.1-mini`, 출력: JSON schema 기반 Structured Outputs
- 인증: `AI_API_KEY` 환경변수 우선, 없으면 Git 루트의 `.env.local`에서 같은 항목 로드
- 요청: 명령별 최대 1회, SDK 자동 재시도 0회, 타임아웃 30초
- API 키 발급: [OpenAI Platform API keys](https://platform.openai.com/api-keys)
- 공식 문서: [모델 지원 기능](https://developers.openai.com/api/docs/models/gpt-4.1-mini),
  [요청 옵션](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)

다른 모델은 temperature/JSON schema 등의 지원 범위가 다를 수 있다. 지원하지 않는
옵션의 API 오류는 안내하고 자동으로 재요청하지 않는다. 제목과 섹션 규칙 위반은 로컬에서
보정하되, 잘린 응답·거절·잘못된 JSON은 실패로 안내한다.

### 검증 명령

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
ruff check .
python -m scripts.demo_safety
```

## 결과물 (Deliverables)

- AI API 연동 및 커밋/PR 초안 생성 흐름을 구현할 Python CLI
- 보너스 과제 수행 결과: [실제 PR #1](https://github.com/myy-dev/B3-2/pull/1), [AI 초안 대비 수정 내역 8줄](docs/PR_CHANGES.md)
