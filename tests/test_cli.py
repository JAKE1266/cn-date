import os
import subprocess
import sys
import unittest


PYTHON = sys.executable
ENV = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}


def run_cli(*args):
    return subprocess.run(
        [PYTHON, "-m", "cn_date", *args],
        capture_output=True,
        env=ENV,
    )


class TestCli(unittest.TestCase):
    def test_version_under_legacy_encoding(self):
        result = run_cli("--version")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.rstrip(b"\r\n"), b"cn-date 0.1.1")
        self.assertEqual(result.stderr, b"")

    def test_help_under_legacy_encoding(self):
        result = run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("中文自然语言日期解析", result.stdout.decode("utf-8"))

    def test_chinese_output_under_legacy_encoding(self):
        result = run_cli("明天下午3点", "--now", "2026-03-04T10:00")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            result.stdout.decode("utf-8").splitlines(),
            ["明天下午3点  →  2026-03-05 15:00  [DT]"],
        )
        self.assertEqual(result.stderr, b"")

    def test_unparseable_text_under_legacy_encoding(self):
        result = run_cli("随便说点什么", "--now", "2026-03-04T10:00")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stdout.decode("utf-8").splitlines(),
            ["随便说点什么  →  无法解析"],
        )

    def test_invalid_now_under_legacy_encoding(self):
        result = run_cli("明天", "--now", "not-a-time")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertIn("--now 需为 ISO 时间", result.stderr.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
