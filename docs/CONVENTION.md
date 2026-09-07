# 팀 커밋·PR 컨벤션

## 확인한 기존 이력

2026-09-06 기준 로컬 저장소에는 다음 두 커밋이 있다.

| 커밋 | 제목 | 관찰 |
| --- | --- | --- |
| `a58c899` | `docs: README 정리 및 설치·시현 가이드 추가` | 영문 유형 접두사, 한국어 설명 |
| `c8fc01d` | `Initial commit` | 초기 생성 커밋 |

이번 구현 PR을 게시하기 전 `gh pr list --repo myy-dev/B3-2 --state all --limit 10`
조회 결과는 빈 배열이었다.
따라서 기존 PR 본문 관례를 추정하지 않는다. 아래 규칙은 확인된 `docs:` 형태를
확장한 이 프로젝트의 명시적인 제안 컨벤션이다. 분석을 위해 이력 전체나 작성자
개인정보를 API에 전달하지 않는다.

## 적용 규칙

- 제목: `type: 한국어 설명`. 유형은 `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.
- 커밋 제목은 50자 이내를 목표로 하고, 72자를 넘지 않는다. 본문은 핵심 변경 1~2개.
- PR 제목은 최대 80자. 본문은 `Why`, `What`, `How to Test`와 각 섹션의 불릿.
- 변경 배경을 diff로 알 수 없으면 작성자 확인이 필요하다고 명시한다.
- 테스트 제안에는 `미실행:`을 붙인다. 이 CLI는 테스트를 실행하지 않는다.
- 잘린 입력의 누락 내용을 추측하지 않으며, 사람이 최종 내용을 보완한다.

```bash
# 기본값: 팀 컨벤션 적용
python main.py commit --convention team
python main.py pr --convention team

# 비교용: 접두사 형식을 강제하지 않음
python main.py commit --convention none
```

프롬프트와 후처리 모두 컨벤션을 적용한다. 모델이 유형을 누락하면 후처리는
`chore:`를 붙이고 검토 안내를 출력한다. 후처리가 변경 유형을 추측하지 않는다.

## 비교 검증 상태

`tests/test_generation.py::test_convention_before_and_after`는 동일한 고정 응답
`입력 검증 추가`를 `none`에서 그대로, `team`에서 `chore: 입력 검증 추가`로
보정하는 것을 검증한다. 이는 로컬 후처리 비교이며 실제 모델 생성 비교가 아니다.

## 실제 OpenAI 생성 비교

2026-09-06, `gpt-4.1-mini`, temperature 0.2, 최대 출력 1200토큰으로 실행했다.
API 요청은 실행당 1회, 컨벤션 비교에 총 2회 사용했다. 두 요청의 변경 컨텍스트가
같음을 SHA-256으로 확인했다. 설정을 바꾼 프롬프트 외 입력은 동일하다.

| 옵션 | 실제 생성 제목 | 길이 |
| --- | --- | --- |
| `--convention none` | README 및 SETUP 문서에 프로젝트 구조와 실행 안내 추가 | 36자 |
| `--convention team` | docs: README 및 SETUP 문서 개선과 실행 안내 추가 | 36자 |

팀 컨벤션 적용 결과는 `docs:` 접두사와 한국어 설명 규칙을 충족하며,
두 결과 모두 권장 길이 50자 이내다. 생성 결과는 모델 특성상 재실행할 때 달라질 수 있다.

원문: [적용 전](examples/live-commit-before.json), [적용 후](examples/live-commit-after.json),
[동일 입력 및 실행 기록](examples/live-run.json).
안전 모드 200줄 제한으로 이 비교의 입력에는 README와 SETUP 변경만 포함되었다.
전체 프로젝트의 변경 설명으로 사용하려면 생략된 코드 변경을 사람이 보완해야 한다.
