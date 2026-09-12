# 안전 정책

## 정규표현식 기반 마스킹

구현 위치: [ai_gitgen/safety.py](../../ai_gitgen/safety.py)의 `PATTERNS`, `ASSIGNMENT`, `mask`

- OpenAI·GitHub·AWS·Slack 키 패턴, JWT, Bearer·Basic 인증 문자열 탐지
- 이메일, URL 내 인증정보, 여러 줄 개인키 블록 탐지
- `api_key`, `secret`, `token`, `password` 등의 대입문에서 값 탐지
- 탐지한 값을 `[REDACTED]`로 치환
- 파일 경로와 diff에 마스킹 적용, 생성 결과에도 안전 모드에 따른 마스킹 적용
- diff를 자르기 전에 전체 파일 diff를 마스킹하여 개인키 블록의 일부 노출 방지
- 정규표현식에 일치하는 패턴만 탐지하므로 모든 민감정보의 탐지 보장은 없음

## diff 전송 제한

구현 위치: [ai_gitgen/git.py](../../ai_gitgen/git.py)의 `collect_changes`

| 제한 기준         | ON                    | OFF                                          |
| ----------------- | --------------------- | -------------------------------------------- |
| 파일 수           | `SAFE_FILES = 10`     | 안전 모드 파일 수 제한 미적용                |
| 전체 diff 줄 수   | `SAFE_LINES = 200`    | 안전 모드 줄 수 제한 미적용                  |
| 전체 diff 문자 수 | `SAFE_CHARS = 20_000` | 내부 상한 `MAX_CONTEXT_CHARS = 200_000` 유지 |

- 민감 파일 제외 후 Git 수집 순서대로 최대 10개 파일 선택
- diff 헤더·주변 문맥을 포함한 전체 diff 기준으로 줄 수 계산
- 파일별 마스킹 후 남은 줄·문자 수 범위로 diff 절단
- 제한 초과 시 `truncated=True` 설정 및 일부 변경 생략 안내 출력
- 제한값은 코드 상수로 관리, CLI 옵션·설정 파일을 통한 조정 기능은 미구현

## ON/OFF 공통 보호

구현 위치: [ai_gitgen/safety.py](../../ai_gitgen/safety.py),
[ai_gitgen/git.py](../../ai_gitgen/git.py), [main.py](../../main.py)

- 실행에 사용하는 실제 API 키는 OFF에서도 문자열 일치로 마스킹
- `.env`, `.env.*`, 자격증명 파일, 개인키 파일, 심볼릭 링크를 내용 수집 전에 제외
- 이름 변경 시 이전 경로와 현재 경로 모두 민감 파일 여부 확인
- ANSI 제어 시퀀스와 화면 표시를 교란하는 제어문자 제거
- 개별 Git 명령 출력이 2,000,000바이트를 초과하면 오류 처리
- 생성 결과의 사용자 검토·수정 및 직접 적용 안내
