import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_install(target: Path, *extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "install.py"), "--target", str(target), *extra_args],
        capture_output=True, text=True, timeout=60,
    )


def test_dry_run_writes_nothing(tmp_path):
    result = run_install(tmp_path, "--dry-run")
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "settings.json").exists()
    assert not any(tmp_path.iterdir())


def test_fresh_install_verifies_guard_and_writes_expected_files(tmp_path):
    result = run_install(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "verify OK" in result.stdout
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / "settings.json").exists()
    assert (tmp_path / "hooks" / "guard_destructive_commands.py").exists()
    assert (tmp_path / "scripts" / "pr_watch.py").exists()
    assert (tmp_path / ".portable-config-manifest.json").exists()

    settings = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert settings["model"] == "opusplan"
    assert settings["hooks"]["PreToolUse"][0]["matcher"] == "Bash|PowerShell"


def test_rerun_is_idempotent_and_upgrades_are_clean(tmp_path):
    run_install(tmp_path)
    before = (tmp_path / "settings.json").read_text(encoding="utf-8")
    result = run_install(tmp_path)
    assert result.returncode == 0, result.stderr
    after = (tmp_path / "settings.json").read_text(encoding="utf-8")
    assert before == after
    assert "verify OK" in result.stdout
