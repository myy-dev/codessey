# feat: Git 변경 기반 AI 커밋·PR 초안 CLI 구현

## Why

- README와 SETUP만 있던 저장소에, 코드 변경 설명을 작성할 수 있는 실행 가능한 Python CLI가 필요했다.
- 초안 생성 비용과 민감정보 전송 범위를 제한하면서 사용자가 결과를 검토하고 직접 적용하도록 한다.

## What

- `commit`, `pr` 명령으로 Git status 및 staged/unstaged/untracked diff를 수집하고 OpenAI 요청을 명령당 1회로 제한한다.
- 커밋 제목 최대 72자, PR 제목 최대 80자 및 필수 섹션/불릿을 로컬에서 검증·보정한다.
- 기본 안전 모드에서 민감정보를 마스킹하고 10파일/200줄/20,000자 제한을 적용한다. 자격증명 파일과 심볼릭 링크는 항상 제외한다.
- `--staged`, `--base`, `--preview`, JSON 출력, 환경변수 및 Git에서 제외한 `.env.local`, 팀 컨벤션을 지원한다.
- 테스트, 설치 안내, 컨벤션 분석과 재현 가능한 안전 모드 비교를 추가한다.
- CLI의 Git 작업은 읽기 전용이다. 커밋·push·PR 생성 기능을 포함하지 않는다.

## How to Test

- 로컬 검증 완료: Python 3.14.5에서 89개 테스트 통과, 코드 커버리지 94%, 린트·포맷·의존성 검사 통과.
- `python -m pip install -r requirements-dev.txt` 후 `python -m pytest -q`를 실행한다.
- `ruff check .`와 `python -m pip check`를 실행한다.
- `python main.py commit --preview`로 API를 호출하지 않고 마스킹·전송 범위를 확인한다.
- `python -m scripts.demo_safety`로 가짜 비밀을 사용하는 ON/OFF 비교를 재현한다.
- 실제 OpenAI 생성 검증 완료: 동일한 안전 모드 컨텍스트에서 커밋 컨벤션 전·후 및 PR 생성에 각각 1회씩 총 3회 성공했다. 제목 길이와 PR 섹션·불릿 규칙을 확인했다.
- 시연 입력은 200줄 제한으로 README/SETUP 변경만 포함했다. 전체 CLI 동작은 위 자동 테스트와 소스 검토로 검증했다.

---

게시 완료: [myy-dev/B3-2 PR #1](https://github.com/myy-dev/B3-2/pull/1). 위 본문이 GitHub에 게시된 내용과 일치함을 확인했다.
이 문서는 [실제 CLI 초안](examples/live-pr-draft.json)을 전체 소스·테스트 검토 결과로 보완한 내용이다.
[초안 대비 수정 내역 8줄](PR_CHANGES.md)을 함께 검토한다.
