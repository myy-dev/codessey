"""원문 기록 없는 입력·터미널 출력 보호 처리."""

from __future__ import annotations

import re
import unicodedata
from pathlib import PurePosixPath

REDACTED = "[REDACTED]"
PATTERNS = (
    # 여러 줄 개인 키 마스킹 시 Git diff 접두사 포함
    re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?"
        r"-----END [A-Z ]*PRIVATE KEY-----"
    ),
    re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,})\b"),
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
    re.compile(r"(?i)\b(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(?<=://)[^\s/:@]+:[^\s/@]+@"),
    re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
)
ASSIGNMENT = re.compile(
    r"""(?ix)
    (\b(?:[a-z0-9]+_)*(?:api[_-]?key|secret|token|password|passwd|private[_-]?key)
    (?:_[a-z0-9]+)*\b["']?\s*[:=]\s*)
    ("[^"\n]*"|'[^'\n]*'|[^\s,;\n]+)
    """
)
ESCAPE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\))")


def terminal_safe(text: str) -> str:
    """줄바꿈·탭 유지, ANSI·제어 문자·양방향 제어 문자 제거."""
    text = ESCAPE.sub("", text)
    return "".join(
        c for c in text if c in "\n\t" or unicodedata.category(c) not in {"Cc", "Cf", "Cs"}
    )


def mask(text: str, api_key: str = "", *, patterns: bool = True) -> str:
    # 안전 모드 OFF에서도 실제 API 키 제거
    if api_key:
        text = text.replace(api_key, REDACTED)
    if patterns:
        for pattern in PATTERNS:
            text = pattern.sub(REDACTED, text)
        text = ASSIGNMENT.sub(lambda m: m[1] + REDACTED, text)
    return terminal_safe(text)


def sensitive_path(path: str) -> bool:
    parts = PurePosixPath(path.replace("\\", "/")).parts
    name = parts[-1].lower() if parts else ""
    return (
        any(part.lower() in {".ssh", ".aws", ".gnupg"} for part in parts)
        or name == ".env"
        or name.startswith(".env.")
        or name.endswith((".pem", ".key", ".p12", ".pfx", ".keystore"))
        or name in {"credentials", "credentials.json", "secrets.json", "id_rsa", "id_ed25519"}
    )
