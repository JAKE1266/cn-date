import os
import subprocess
import sys
import sysconfig
import tempfile
from datetime import datetime
from importlib import metadata
from pathlib import Path

import cn_date


def main() -> None:
    dist = metadata.distribution("cn-date")
    assert dist.metadata["Name"] == "cn-date"
    assert dist.version == "0.1.1"
    assert cn_date.__version__ == "0.1.1"
    assert dist.metadata["Requires-Python"] == ">=3.8"
    assert not dist.requires

    source_root = Path(__file__).resolve().parent.parent
    module_path = Path(cn_date.__file__).resolve()
    assert source_root not in module_path.parents, module_path

    now = datetime(2026, 3, 4, 10, 0)
    assert cn_date.parse_dt("明天下午3点", now) == datetime(2026, 3, 5, 15, 0)
    assert cn_date.parse_dt("中午24点", now) is None
    assert cn_date.parse_dt("10点123分", now) is None
    assert cn_date.parse_dt("0号", now) is None
    assert cn_date.parse_dt("明天123点", now) is None
    assert cn_date.parse_dt("明天0号", now) is None

    executable = Path(sysconfig.get_path("scripts")) / (
        "cn-date.exe" if os.name == "nt" else "cn-date"
    )
    assert executable.is_file(), executable

    env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
    with tempfile.TemporaryDirectory() as workdir:
        result = subprocess.run(
            [sys.executable, "-m", "cn_date", "明天下午3点", "--now", "2026-03-04T10:00"],
            capture_output=True, cwd=workdir, env=env, check=True,
        )
        assert result.stdout.decode("utf-8").splitlines() == [
            "明天下午3点  →  2026-03-05 15:00  [DT]"
        ]
        assert result.stderr == b""

        invalid = subprocess.run(
            [sys.executable, "-m", "cn_date", "中午24点", "--now", "2026-03-04T10:00"],
            capture_output=True, cwd=workdir, env=env,
        )
        assert invalid.returncode == 1
        assert "无法解析" in invalid.stdout.decode("utf-8")

        bad_now = subprocess.run(
            [sys.executable, "-m", "cn_date", "明天", "--now", "not-a-time"],
            capture_output=True, cwd=workdir, env=env,
        )
        assert bad_now.returncode == 2
        assert "--now 需为 ISO 时间" in bad_now.stderr.decode("utf-8")

        console = subprocess.run(
            [str(executable), "下周一上午9点", "--now", "2026-03-04T10:00"],
            capture_output=True, cwd=workdir, env=env, check=True,
        )
        assert console.stdout.decode("utf-8").splitlines() == [
            "下周一上午9点  →  2026-03-09 09:00  [DT]"
        ]

    print("installed cn-date 0.1.1 smoke: OK")


if __name__ == "__main__":
    main()
