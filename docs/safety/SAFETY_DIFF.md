# 안전 모드 ON/OFF 전송 diff 원문

## 기록 범위

- 실제 OpenAI 요청 JSON의 `context.diff` 문자열 전체 기록, 줄바꿈 표시 복원
- 동일한 미커밋 `welcome_email.py`에 대한 모드별 입력
- 두 모드 모두 1개 파일·26줄 전송, 잘림·생략 없음
- 이메일·비밀번호는 시연용 값, diff에 실제 자격증명 포함 없음
- 생성 결과: [안전 모드 비교](SAFETY_COMPARISON.md)
- 구현 내용: [안전 정책](SAFETY.md)

## OFF 전송 원문

이메일·비밀번호 값을 유지한 diff:

```diff
diff --git a/welcome_email.py b/welcome_email.py
new file mode 100644
index 0000000..84282d9
--- /dev/null
+++ b/welcome_email.py
@@ -0,0 +1,20 @@
+"""Welcome email example. All configuration values are demonstration-only."""
+
+MAIL_SETTINGS = {
+    "smtp_host": "smtp.example.test",
+    "sender_email": "sender@example.test",
+    "smtp_password": "DEMO_ONLY_PASSWORD",
+}
+
+
+def build_welcome_email(recipient_email: str, display_name: str) -> dict:
+    if not recipient_email or "@" not in recipient_email:
+        raise ValueError("Recipient email is required")
+    if not display_name.strip():
+        raise ValueError("Display name is required")
+    return {
+        "from": MAIL_SETTINGS["sender_email"],
+        "to": recipient_email,
+        "subject": f"Welcome, {display_name.strip()}!",
+        "body": "Your account is ready. You can now sign in.",
+    }
```

## ON 전송 원문

이메일·비밀번호 값을 `[REDACTED]`로 치환한 diff:

```diff
diff --git a/welcome_email.py b/welcome_email.py
new file mode 100644
index 0000000..84282d9
--- /dev/null
+++ b/welcome_email.py
@@ -0,0 +1,20 @@
+"""Welcome email example. All configuration values are demonstration-only."""
+
+MAIL_SETTINGS = {
+    "smtp_host": "smtp.example.test",
+    "sender_email": "[REDACTED]",
+    "smtp_password": [REDACTED],
+}
+
+
+def build_welcome_email(recipient_email: str, display_name: str) -> dict:
+    if not recipient_email or "@" not in recipient_email:
+        raise ValueError("Recipient email is required")
+    if not display_name.strip():
+        raise ValueError("Display name is required")
+    return {
+        "from": MAIL_SETTINGS["sender_email"],
+        "to": recipient_email,
+        "subject": f"Welcome, {display_name.strip()}!",
+        "body": "Your account is ready. You can now sign in.",
+    }
```

## 변경 지점

| 필드 | OFF | ON |
| --- | --- | --- |
| `sender_email` | `"sender@example.test"` | `"[REDACTED]"` |
| `smtp_password` | `"DEMO_ONLY_PASSWORD"` | `[REDACTED]` |

- 이메일 정규표현식: 문자열 내부 이메일만 치환, 따옴표 유지
- 비밀번호 대입문 정규표현식: 따옴표를 포함한 값 전체 치환
- 위 두 줄 외 diff 내용 동일
- ON 원문은 코드 실행용이 아닌 AI 분석용 텍스트
