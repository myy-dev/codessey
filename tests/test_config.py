from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_leak_app.config import Config, ConfigError, parse_bool


FLOAT_FIELDS = {
    "AGENT_RUN_SECONDS": "run_seconds",
    "LEAK_INTERVAL": "leak_interval",
    "WATCHDOG_INTERVAL": "watchdog_interval",
    "SCHEDULER_QUANTUM": "scheduler_quantum",
}


class ConfigTest(unittest.TestCase):
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
        self.env = {
            "AGENT_HOME": str(home),
            "AGENT_UPLOAD_DIR": str(upload),
            "AGENT_KEY_PATH": str(keys),
            "AGENT_LOG_DIR": str(logs),
            "AGENT_PORT": "15034",
            "MEMORY_LIMIT": "50",
            "CPU_MAX_OCCUPY": "10",
            "MULTI_THREAD_ENABLE": "true",
        }

    def test_valid_configuration(self) -> None:
        config = Config.from_env(self.env, euid=1000)
        self.assertEqual(config.port, 15034)
        self.assertEqual(config.memory_limit_mb, 50)
        self.assertTrue(config.multi_thread_enable)

    def test_root_user_is_rejected(self) -> None:
        with self.assertRaisesRegex(ConfigError, "non-root"):
            Config.from_env(self.env, euid=0)

    def test_wrong_fixed_port_is_rejected(self) -> None:
        self.env["AGENT_PORT"] = "15035"
        with self.assertRaisesRegex(ConfigError, "must be 15034"):
            Config.from_env(self.env, euid=1000)

    def test_memory_limit_range_is_enforced(self) -> None:
        self.env["MEMORY_LIMIT"] = "49"
        with self.assertRaisesRegex(ConfigError, "between 50 and 512"):
            Config.from_env(self.env, euid=1000)

    def test_cpu_limit_range_is_enforced(self) -> None:
        self.env["CPU_MAX_OCCUPY"] = "101"
        with self.assertRaisesRegex(ConfigError, "between 10 and 100"):
            Config.from_env(self.env, euid=1000)

    def test_non_finite_time_settings_are_rejected(self) -> None:
        for name in FLOAT_FIELDS:
            for value in ("nan", "inf", "-inf"):
                with self.subTest(name=name, value=value):
                    env = {**self.env, name: value}
                    with self.assertRaisesRegex(ConfigError, f"{name} must be finite"):
                        Config.from_env(env, euid=1000)

    def test_finite_positive_time_settings_are_accepted(self) -> None:
        for name, attribute in FLOAT_FIELDS.items():
            for value in ("0.001", "1.25", "100"):
                with self.subTest(name=name, value=value):
                    config = Config.from_env({**self.env, name: value}, euid=1000)
                    self.assertEqual(getattr(config, attribute), float(value))

    def test_secret_content_is_enforced(self) -> None:
        (Path(self.env["AGENT_KEY_PATH"]) / "secret.key").write_text("wrong\n", encoding="utf-8")
        with self.assertRaisesRegex(ConfigError, "content"):
            Config.from_env(self.env, euid=1000)

    def test_required_directory_must_exist(self) -> None:
        self.env["AGENT_LOG_DIR"] = str(Path(self.temporary.name) / "missing-logs")
        with self.assertRaisesRegex(ConfigError, "does not exist"):
            Config.from_env(self.env, euid=1000)

    def test_log_directory_must_be_writable(self) -> None:
        log_dir = Path(self.env["AGENT_LOG_DIR"])
        log_dir.chmod(0o500)
        with self.assertRaisesRegex(ConfigError, "not writable"):
            Config.from_env(self.env, euid=1000)

    def test_upload_path_must_be_under_agent_home(self) -> None:
        different_upload = Path(self.temporary.name) / "different-upload"
        different_upload.mkdir()
        self.env["AGENT_UPLOAD_DIR"] = str(different_upload)
        with self.assertRaisesRegex(ConfigError, "must be.*upload_files"):
            Config.from_env(self.env, euid=1000)

    def test_boolean_aliases(self) -> None:
        for value in ("true", "1", "yes"):
            self.assertTrue(parse_bool(value))
        for value in ("false", "0", "no"):
            self.assertFalse(parse_bool(value))
        with self.assertRaises(ConfigError):
            parse_bool("enabled")


if __name__ == "__main__":
    unittest.main()
