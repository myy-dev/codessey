from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(os.geteuid() == 0, "the lab intentionally rejects root")
class BootIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        home = Path(self.temporary.name) / "agent-home"
        upload = home / "upload_files"
        keys = home / "api_keys"
        logs = Path(self.temporary.name) / "logs"
        upload.mkdir(parents=True)
        keys.mkdir(parents=True)
        logs.mkdir()
        (keys / "secret.key").write_text("agent_api_key_test\n", encoding="utf-8")
        self.env = os.environ.copy()
        self.env.update(
            {
                "PYTHONPATH": str(ROOT / "src"),
                "AGENT_HOME": str(home),
                "AGENT_UPLOAD_DIR": str(upload),
                "AGENT_KEY_PATH": str(keys),
                "AGENT_LOG_DIR": str(logs),
                "AGENT_PORT": "15034",
                "MEMORY_LIMIT": "50",
                "CPU_MAX_OCCUPY": "20",
                "MULTI_THREAD_ENABLE": "false",
                "AGENT_SCENARIO": "normal",
                "SCHEDULER_QUANTUM": "0.001",
            }
        )

    def run_app(self, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "agent_leak_app"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

    def test_missing_required_environment_fails_before_boot(self) -> None:
        del self.env["AGENT_HOME"]
        completed = self.run_app(self.env)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("AGENT_HOME is required", completed.stderr)

    def test_occupied_fixed_port_fails_boot(self) -> None:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("0.0.0.0", 15034))
        listener.listen(1)
        self.addCleanup(listener.close)

        completed = self.run_app(self.env)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("cannot bind 0.0.0.0:15034", completed.stdout)

    def test_valid_boot_binds_and_completes(self) -> None:
        completed = self.run_app(self.env)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("[BOOT] SUCCESS", completed.stdout)
        self.assertIn("bind=0.0.0.0:15034", completed.stdout)


if __name__ == "__main__":
    unittest.main()
