# 설치 및 시연

## 빠른 실행

Python 3.10 이상과 Git이 필요하다. 프로젝트 루트에서 실행한다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

프로젝트 루트의 `.env`에 본인 키를 입력한다. 이 파일은 Git에서 제외된다.
프로그램은 `load_dotenv()`로 설정을 환경변수에 로드한다.

```dotenv
AI_API_KEY=본인의_OpenAI_API_키
```

키 발급처: [OpenAI Platform](https://platform.openai.com/api-keys).
셸에 `AI_API_KEY` 환경변수가 있으면 `.env`보다 우선한다.

## 커밋·PR 생성 시연

아직 커밋하지 않은 Git 변경이 있는 상태에서 실행한다.
수집 범위는 staged + unstaged + untracked다. 변경이 없으면 안내 후 API 호출 없이 종료한다.

```bash
# 실제 생성: 명령당 API 1회
python main.py commit --safe-mode
python main.py pr --safe-mode

# 모델·옵션 적용
python main.py commit --model gpt-4.1-mini --temperature 0.2 --max-tokens 1200
```

출력에서 변경 요약, 제목·본문, API 요청 횟수를 확인한다. 커밋 제목은 최대 72자,
PR 제목은 최대 80자다. PR 본문에는 `Why`, `What`, `How to Test`와 각 섹션의 불릿이 포함된다.
생성 결과를 검토·수정한 뒤 직접 사용한다. 프로그램은 커밋·push·PR 게시를 실행하지 않는다.

## 안전 모드 비교

안전 모드는 기본 ON이다. 키·이메일·비밀번호·개인키 등을 정규표현식으로 마스킹한 뒤
최대 10파일·200줄·20,000자만 전송한다. 내용이 잘리면 생략 안내를 출력한다.
`--no-safe-mode`로 패턴 마스킹과 안전 모드 전용 상한을 해제할 수 있다.
실제 실행 키, 자격증명 파일과 심볼릭 링크는 두 모드 모두 보호한다.
패턴에 없는 비밀은 남을 수 있으므로 실행 전에 변경 파일의 내용을 확인한다.

```bash
# 가짜 키·이메일·비밀번호를 사용한 비교: API 호출 없음
python -m scripts.demo_safety
```

| 확인 항목 | OFF | ON |
| --- | --- | --- |
| 일반 파일 전송 수 | 13 | 10 |
| 자격증명 파일 제외 | 1 | 1 |
| 파일 제한으로 생략 | 0 | 3 |
| 가짜 키·이메일·비밀번호 | 보임 | 마스킹 |

## 테스트와 과제 기록

```bash
# 실제 API를 호출하지 않는 자동 테스트
python -m pytest -q
```

- 자동 테스트: 85개 통과. Git 수집, 출력 형식, 안전 모드, API 오류·호출 횟수 검증.
- [팀 컨벤션 및 실제 생성 전·후 비교](docs/CONVENTION.md)
- [안전 모드 비교 결과](docs/examples/safety-comparison.json)
- [실제 OpenAI 생성 3회 기록](docs/examples/live-run.json)
- [AI 초안 대비 최종 PR 수정 내역 8줄](docs/PR_CHANGES.md)
- [실제 PR #1](https://github.com/myy-dev/B3-2/pull/1)

실제 API 시연은 안전 모드의 200줄 제한으로 README/SETUP 변경만 포함했다.
전체 CLI 동작은 자동 테스트로 확인했다. 생성 결과 파일은 당시의 시연 원문이다.
