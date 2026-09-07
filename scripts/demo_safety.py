"""Offline safety comparison using synthetic data only. Makes zero API requests."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from ai_gitgen.git import collect_changes


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ai-gitgen-safety-") as directory:
        root = Path(directory)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        synthetic_key = "sk-proj-" + "FAKE_DEMO_NOT_A_REAL_KEY" * 2
        (root / "00-settings.txt").write_text(
            f'api_key = "{synthetic_key}"\nemail = "demo@example.test"\n'
            'password = "FAKE_DEMO_PASSWORD"\n',
            encoding="utf-8",
        )
        for i in range(1, 13):
            (root / f"{i:02}-change.txt").write_text(f"change {i}\n", encoding="utf-8")
        (root / ".env.secret").write_text("never_sent_in_either_mode\n", encoding="utf-8")
        result = {"fixture": "synthetic data only; no real credentials", "api_calls": 0}
        for safe, label in ((False, "off"), (True, "on")):
            context = collect_changes(root, safe=safe)
            result[label] = {
                "total_files": context.total_files,
                "sent_files": len(context.files),
                "excluded_files": context.excluded_files,
                "omitted_files": context.omitted_files,
                "diff_lines": len(context.diff.splitlines()),
                "truncated": context.truncated,
                "synthetic_key_visible": synthetic_key in context.diff,
                "email_visible": "demo@example.test" in context.diff,
                "password_visible": "FAKE_DEMO_PASSWORD" in context.diff,
                "credential_file_visible": "never_sent_in_either_mode" in context.diff,
            }
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
