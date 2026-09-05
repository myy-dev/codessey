# 설치 및 실행 방법

이 문서는 프로젝트 설치·실행 방법과 프로젝트 시현 내용을 정리합니다.

## 사전 요구사항

- Python 3.10 이상
- Git
- OpenAI API Key

## 1. 저장소 복제 및 이동

```bash
git clone https://github.com/myy-dev/B6-2.git
cd B6-2
```

## 2. 가상환경 생성 및 활성화

가상환경 사용을 권장합니다.

macOS 또는 Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## 3. 의존성 설치

```bash
python -m pip install -r requirements.txt
```

## 4. API Key 설정

macOS 또는 Linux:

```bash
export AI_API_KEY="YOUR_API_KEY"
```

Windows PowerShell:

```powershell
$env:AI_API_KEY="YOUR_API_KEY"
```

API Key를 소스 코드, 로그, README 또는 Git 이력에 포함하지 않습니다.

## 5. 실행

커밋 메시지 생성:

```bash
python main.py commit
```

Pull Request 제목·본문 생성:

```bash
python main.py pr
```

옵션 적용 예시:

```bash
python main.py commit --model MODEL_NAME --temperature 0.2 --max-tokens 500 --safe-mode
python main.py pr --model MODEL_NAME --temperature 0.2 --max-tokens 1000 --safe-mode
```

## 프로젝트 시현

### 시현 준비

1. Git이 초기화된 프로젝트에서 의미 있는 변경 사항을 만듭니다.
2. `git status`와 `git diff`로 변경 사항을 확인합니다.
3. API Key와 실행 옵션을 확인합니다.

### 커밋 메시지 생성 시현

```bash
python main.py commit --safe-mode
```

확인 내용:

- Git 변경 사항 수집
- OpenAI API 요청
- 변경 요약 및 커밋 메시지 출력
- 생성 결과 검토

### Pull Request 초안 생성 시현

```bash
python main.py pr --safe-mode
```

확인 내용:

- Git 변경 사항 및 변경 맥락 반영
- PR 제목과 `Why`, `What`, `How to Test` 본문 생성
- 제목 길이와 필수 섹션 검증
- 생성 결과 검토

### 시현 기록

- 시현 일시: 구현 후 기록
- 시현 브랜치: 구현 후 기록
- 실행 결과: 구현 후 기록
- 실제 PR 링크: 구현 후 기록
- AI 초안 대비 최종 수정 내역: 구현 후 기록
