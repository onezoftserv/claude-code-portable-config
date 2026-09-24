import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import install as inst  # noqa: E402


def fresh_manifest():
    return {"files": {}, "permission_rules": {}}


def test_fresh_write_records_hash(tmp_path):
    src = tmp_path / "src.md"
    src.write_text("v1\n", encoding="utf-8")
    dst = tmp_path / "target" / "CLAUDE.md"
    manifest = fresh_manifest()

    inst.sync_managed_file(src, dst, "CLAUDE.md", manifest, force=False, dry_run=False)

    assert dst.read_text(encoding="utf-8") == "v1\n"
    assert manifest["files"]["CLAUDE.md"] == inst.file_hash("v1\n")


def test_rerun_unchanged_is_a_noop(tmp_path):
    src = tmp_path / "src.md"
    src.write_text("v1\n", encoding="utf-8")
    dst = tmp_path / "target" / "CLAUDE.md"
    manifest = fresh_manifest()
    inst.sync_managed_file(src, dst, "CLAUDE.md", manifest, force=False, dry_run=False)

    inst.sync_managed_file(src, dst, "CLAUDE.md", manifest, force=False, dry_run=False)
    assert dst.read_text(encoding="utf-8") == "v1\n"
    assert not list(tmp_path.rglob("*.bak"))


def test_untouched_file_upgrades_on_source_change(tmp_path):
    src = tmp_path / "src.md"
    src.write_text("v1\n", encoding="utf-8")
    dst = tmp_path / "target" / "CLAUDE.md"
    manifest = fresh_manifest()
    inst.sync_managed_file(src, dst, "CLAUDE.md", manifest, force=False, dry_run=False)

    src.write_text("v2\n", encoding="utf-8")
    inst.sync_managed_file(src, dst, "CLAUDE.md", manifest, force=False, dry_run=False)

    assert dst.read_text(encoding="utf-8") == "v2\n"
    assert len(list(tmp_path.rglob("*.bak"))) == 1


def test_hand_edited_file_is_skipped_without_force(tmp_path):
    src = tmp_path / "src.md"
    src.write_text("v1\n", encoding="utf-8")
    dst = tmp_path / "target" / "CLAUDE.md"
    manifest = fresh_manifest()
    inst.sync_managed_file(src, dst, "CLAUDE.md", manifest, force=False, dry_run=False)

    dst.write_text("MY OWN NOTES\n", encoding="utf-8")  # hand-edit
    src.write_text("v2\n", encoding="utf-8")  # source also changed upstream
    inst.sync_managed_file(src, dst, "CLAUDE.md", manifest, force=False, dry_run=False)

    assert dst.read_text(encoding="utf-8") == "MY OWN NOTES\n", "hand-edited file must not be clobbered"
    assert not list(tmp_path.rglob("*.bak"))


def test_force_overwrites_hand_edit_with_timestamped_backup(tmp_path):
    src = tmp_path / "src.md"
    src.write_text("v1\n", encoding="utf-8")
    dst = tmp_path / "target" / "CLAUDE.md"
    manifest = fresh_manifest()
    inst.sync_managed_file(src, dst, "CLAUDE.md", manifest, force=False, dry_run=False)

    dst.write_text("MY OWN NOTES\n", encoding="utf-8")
    src.write_text("v2\n", encoding="utf-8")
    inst.sync_managed_file(src, dst, "CLAUDE.md", manifest, force=True, dry_run=False)

    assert dst.read_text(encoding="utf-8") == "v2\n"
    backups = list(tmp_path.rglob("CLAUDE.md.*.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "MY OWN NOTES\n"


def test_dry_run_never_writes_or_creates_directories(tmp_path):
    src = tmp_path / "src.md"
    src.write_text("v1\n", encoding="utf-8")
    dst = tmp_path / "target" / "CLAUDE.md"
    manifest = fresh_manifest()

    inst.sync_managed_file(src, dst, "CLAUDE.md", manifest, force=False, dry_run=True)

    assert not dst.exists()
    assert not dst.parent.exists()
    assert "CLAUDE.md" not in manifest["files"]


def test_remove_renamed_file_removes_untouched_old_file(tmp_path):
    # Simulates commands/resume.md -> pickup.md: the old file must go away
    # on upgrade, not linger and keep shadowing Claude Code's built-in
    # /resume command forever.
    manifest = fresh_manifest()
    old = tmp_path / "commands" / "resume.md"
    old.parent.mkdir(parents=True)
    old.write_text("old content\n", encoding="utf-8")
    manifest["files"]["commands/resume.md"] = inst.file_hash("old content\n")

    inst.remove_renamed_file(tmp_path, "commands/resume.md", manifest, dry_run=False)

    assert not old.exists()
    assert "commands/resume.md" not in manifest["files"]


def test_remove_renamed_file_keeps_a_hand_edited_old_file(tmp_path):
    manifest = fresh_manifest()
    old = tmp_path / "commands" / "resume.md"
    old.parent.mkdir(parents=True)
    old.write_text("hand-edited content\n", encoding="utf-8")
    manifest["files"]["commands/resume.md"] = inst.file_hash("original content\n")  # doesn't match current

    inst.remove_renamed_file(tmp_path, "commands/resume.md", manifest, dry_run=False)

    assert old.exists()
    assert old.read_text(encoding="utf-8") == "hand-edited content\n"


def test_remove_renamed_file_is_a_noop_when_never_installed(tmp_path):
    manifest = fresh_manifest()
    inst.remove_renamed_file(tmp_path, "commands/resume.md", manifest, dry_run=False)
    assert not (tmp_path / "commands" / "resume.md").exists()
