# 사용자 시연 예시

## CLI 도움말

```bash
python main.py --help
python main.py commit --help
python main.py pr --help
```

## 커밋 메시지 초안 생성

```bash
python main.py commit
```

## Pull Request 초안 생성

```bash
python main.py pr
```

## 생성 옵션 적용

```bash
python main.py commit --model gpt-4.1-mini --temperature 0.2 --max-tokens 1200
python main.py pr --model gpt-4.1-mini --temperature 0.2 --max-tokens 1200
```

## 컨벤션 적용

```bash
python main.py commit --convention team
python main.py pr --convention none
```

## 안전 모드 적용

```bash
python main.py commit --safe-mode
python main.py pr --safe-mode
```
