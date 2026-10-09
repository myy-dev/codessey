from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def submitted_evidence_hashes() -> dict[Path, str]:
    return {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for directory in (ROOT / "evidence" / "generated", ROOT / "evidence" / "charts")
        for path in directory.iterdir()
        if path.is_file()
    }


@unittest.skipIf(os.geteuid() == 0, "the lab intentionally rejects root")
class ExperimentIntegrationTest(unittest.TestCase):
    def test_all_experiments_generate_expected_evidence(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="agent experiments ")
        self.addCleanup(temporary.cleanup)
        output_root = Path(temporary.name)
        submitted_files = submitted_evidence_hashes()
        completed = subprocess.run(
            [sys.executable, "scripts/run_experiments.py", "--output-root", str(output_root)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

        summary_path = output_root / "evidence" / "generated" / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        by_name = {item["name"]: item for item in summary["experiments"]}

        self.assertEqual(by_name["oom-before"]["exit_code"], 137)
        self.assertEqual(by_name["oom-after"]["exit_code"], 0)
        self.assertEqual(by_name["cpu-before"]["exit_code"], 143)
        self.assertEqual(by_name["cpu-after"]["exit_code"], 0)
        self.assertTrue(by_name["deadlock-before"]["timed_out_while_alive"])
        self.assertEqual(by_name["deadlock-after"]["exit_code"], 0)
        self.assertEqual(by_name["scheduling-round-robin"]["exit_code"], 0)

        manifest_path = output_root / "evidence" / "generated" / "manifest.sha256.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertIn("evidence/generated/summary.json", manifest)
        self.assertEqual(len(manifest), 21)
        for path, expected in manifest.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((output_root / path).read_bytes()).hexdigest(), expected)

        completed = subprocess.run(
            [sys.executable, "scripts/generate_charts.py", "--output-root", str(output_root)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8")), manifest)
        self.assertEqual(submitted_evidence_hashes(), submitted_files,
                         "tests must preserve submitted evidence")


if __name__ == "__main__":
    unittest.main()
