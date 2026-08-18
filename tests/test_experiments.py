from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(os.geteuid() == 0, "the lab intentionally rejects root")
class ExperimentIntegrationTest(unittest.TestCase):
    def test_all_experiments_generate_expected_evidence(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/run_experiments.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

        summary_path = ROOT / "evidence" / "generated" / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        by_name = {item["name"]: item for item in summary["experiments"]}

        self.assertEqual(by_name["oom-before"]["exit_code"], 137)
        self.assertEqual(by_name["oom-after"]["exit_code"], 0)
        self.assertEqual(by_name["cpu-before"]["exit_code"], 143)
        self.assertEqual(by_name["cpu-after"]["exit_code"], 0)
        self.assertTrue(by_name["deadlock-before"]["timed_out_while_alive"])
        self.assertEqual(by_name["deadlock-after"]["exit_code"], 0)
        self.assertEqual(by_name["scheduling-round-robin"]["exit_code"], 0)

        manifest = json.loads(
            (ROOT / "evidence" / "generated" / "manifest.sha256.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("evidence/generated/summary.json", manifest)


if __name__ == "__main__":
    unittest.main()
