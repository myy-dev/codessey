# 팀 커밋·PR 컨벤션

## 기존 이력 확인

| 커밋      | 제목                                         | 관찰                          |
| --------- | -------------------------------------------- | ----------------------------- |
| `a58c899` | `docs: README 정리 및 설치·시현 가이드 추가` | 영문 유형 접두사, 한국어 설명 |
| `c8fc01d` | `Initial commit`                             | 초기 생성 커밋                |

## 적용 규칙

- 제목 `type: 한국어 설명`, 유형 `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
- 커밋 제목 50자 이내 목표, 최대 72자, 본문 핵심 변경 1~2개
- PR 제목 최대 80자, 본문 `Why`, `What`, `How to Test` 및 섹션별 불릿
- diff로 확인할 수 없는 변경 배경의 작성자 확인 필요 명시
- 테스트 제안의 `미실행:` 표기, CLI 테스트 미실행
- 잘린 입력의 누락 내용 추측 제외, 최종 내용의 작성자 보완

```bash
# 기본값: 팀 컨벤션 적용
python main.py commit --convention team
python main.py pr --convention team

# 비교용: 접두사 형식을 강제하지 않음
python main.py commit --convention none
```

## 실제 OpenAI 생성 비교

2026-09-06, `gpt-4.1-mini`, temperature 0.2, 최대 출력 1200토큰 실행 조건
API 요청 실행당 1회, 컨벤션 비교 총 2회
두 요청의 변경 컨텍스트 SHA-256 일치 확인
설정 변경 프롬프트 외 입력 동일

| 옵션                | 실제 생성 제목                                        | 길이 |
| ------------------- | ----------------------------------------------------- | ---- |
| `--convention none` | README 및 SETUP 문서에 프로젝트 구조와 실행 안내 추가 | 36자 |
| `--convention team` | docs: README 및 SETUP 문서 개선과 실행 안내 추가      | 36자 |

팀 컨벤션 적용 결과의 `docs:` 접두사 및 한국어 설명 규칙 충족
두 결과의 권장 길이 50자 이내
재실행 시 모델 특성에 따른 생성 결과 변경 가능성

원문 [적용 전](examples/live-commit-before.json), [적용 후](examples/live-commit-after.json),
[동일 입력 및 실행 기록](examples/live-run.json)
안전 모드 200줄 제한에 따른 README와 SETUP 변경 입력
전체 프로젝트 변경 설명 시 생략 코드 변경의 작성자 보완
