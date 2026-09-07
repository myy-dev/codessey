# 구현 검증 기록

검증 환경: 2026-09-06, macOS ARM64, Python 3.14.5, Git 저장소 `myy-dev/B3-2`.
구현은 Python 3.10 문법을 대상으로 한다. 아래 로컬 검증과 실제 외부 API 검증을 구분한다.

최종 로컬 결과: **89개 테스트 통과, 코드 커버리지 94%**, Ruff 린트·포맷 검사 통과,
설치 의존성 검사 통과. Python 파일 14개가 Python 3.10 문법 검사에 통과했다.
Python 3.10 인터프리터에서의 실제 실행은 아직 수행하지 않았으며 실행 테스트 환경은
Python 3.14.5다. 실제 키가 Git에서 제외되지 않은 파일, 기존 Git 이력, 전송 미리보기에
포함되지 않았음을 값 비출력 방식으로 확인했다.

## 요구사항별 근거

| README 요구사항 | 구현·검증 근거 |
| --- | --- |
| Git 루트, status/diff, 변경 없음/오류 처리 | `ai_gitgen/git.py`, `tests/test_git.py`, `tests/test_cli.py` |
| 신규·스테이징·일반 변경, 삭제/이름 변경/바이너리 | 실제 임시 Git 저장소로 통합 테스트 |
| 환경변수·키 비노출 | `load_api_key`, .gitignore, 환경변수 우선/파일 비실행/출력 마스킹 테스트 |
| AI 요청·옵션·원인별 오류 | 실제 OpenAI SDK와 `httpx.MockTransport`로 요청 JSON/오류 응답 검증 |
| 명령당 1회·자동 재시도 없음 | commit/pr 성공, HTTP 400/401/403/404/429/500, 연결/시간초과 테스트 |
| 제목 길이·본문 불릿·PR 섹션 | `normalize`, `validate`, 빈 필드·긴 제목·잘못된 본문 테스트 |
| 재생성 없는 로컬 보정 | 보정 안내 목록과 최종 유효성 검증 |
| 안전 모드·고도화·ON/OFF 비교 | `tests/test_safety.py`, `scripts/demo_safety.py`, `docs/SAFETY.md` |
| 변경 요약·복사 구획·검토 안내 | commit/pr 텍스트 및 JSON 출력 통합 테스트 |
| 팀 컨벤션 분석·적용 | `docs/CONVENTION.md`, `--convention`, 프롬프트 및 후처리 테스트 |
| 실제 API 인증 | 모델 조회 HTTP 200, `docs/examples/authentication.json` |
| 실제 초안·모델 생성 비교 | **성공**: `docs/examples/live-run.json`, 3회 요청, 출력 규칙 및 동일 입력 검증 |
| 실제 PR·최종 PR 수정 내역 | **완료**: [PR #1](https://github.com/myy-dev/B3-2/pull/1), `docs/PR_CHANGES.md` 8줄, 게시 본문 일치 확인 |

## 로컬 실행

```bash
python -m pytest --cov=ai_gitgen --cov=main --cov-report=term-missing -q
ruff check .
ruff format --check .
python -m pip check
git diff --check
```

테스트는 합성 API 키와 가짜 응답만 사용하고 실제 API 비용을 발생시키지 않는다.
CLI Git 수집 전후의 status와 인덱스 바이트가 동일함을 확인한다.

## 외부 검증 상태

사용자의 키 확인 요청에 따라 `.env.local`의 설정과 CLI 로드를 점검하고,
`GET /v1/models/gpt-4.1-mini` 요청 1회에서 HTTP 200으로 인증 및 모델 조회 성공을 확인했다.
키 값이나 응답 원문을 기록하지 않았으며 이 요청에는 저장소 내용을 포함하지 않았다.
기록: [authentication.json](examples/authentication.json).

사용자가 저장소 내용의 OpenAI 전송 및 생성 검증 총 3회를 명시적으로 승인한 후,
안전 모드에서 커밋 컨벤션 전·후와 PR 초안을 각각 1회 생성했다. 세 실행 모두 성공했고
SDK 재시도는 0회다. 세 제목은 모두 36자로 길이 규칙을 충족했으며 PR의 필수 세 섹션과
섹션별 불릿을 검증했다. 입력 컨텍스트 SHA-256은 세 요청 사이에 동일했다.

기록: [실행 메타데이터](examples/live-run.json), [PR 생성 결과](examples/live-pr-draft.json).
인증용 모델 조회 1회는 별도이며 생성 요청 3회에 포함하지 않는다.

안전 모드 200줄 제한으로 README/SETUP의 변경만 모델에 전달되었다. 출력의
`truncated: true`와 생략 안내를 확인했고, 전체 기능 설명은 소스와 테스트를 직접 검토하여
[최종 PR 검토 본문](PR_DRAFT.md)에 보완했다. [수정 내역](PR_CHANGES.md)은 8줄이다.
사용자가 필수 섹션과 불릿 확인 후 게시하도록 승인하여 [PR #1](https://github.com/myy-dev/B3-2/pull/1)을 생성했다.
GitHub에서 다시 조회한 본문에 Why/What/How to Test 헤더가 각각 한 번 있고,
불릿이 각각 2/6/7개임을 확인했다. 게시 본문은 검토 본문과 일치하며 PR은 OPEN 상태다.

## 원격 저장소 확인

GitHub의 `myy-dev/B3-2` 초기 커밋 `c8fc01d`가 현재 로컬 이력과 일치함을 확인했다.
로컬 origin에 남아 있던 B6-2 주소를 B3-2로 수정했다. B6-2는 별도 FastAPI 프로젝트이므로
이 작업의 게시 대상에서 제외한다. 기본 브랜치는 `main`이며 이번 PR 게시 전 기존 PR 조회 결과는 빈 배열이었다.
실제 API 시연 당시의 입력과 생성 결과 스냅샷은 변경하지 않았다.
