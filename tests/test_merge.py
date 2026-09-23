import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import install as inst  # noqa: E402


def fresh_manifest():
    return {"files": {}, "settings_keys": {}, "permission_rules": {}}


def test_first_run_adopts_base_values():
    base = {"model": "opusplan", "permissions": {"allow": ["Bash(git status)"]}}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"))
    assert merged["model"] == "opusplan"
    assert "Bash(git status)" in merged["permissions"]["allow"]


def test_rerun_with_unchanged_base_is_idempotent():
    base = {"model": "opusplan", "permissions": {"allow": ["Bash(git status)"]}}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"))
    merged2, _ = inst.merge_settings(base, merged, manifest, Path("/hooks"))
    assert merged == merged2


def test_base_change_upgrades_when_untouched_locally():
    base = {"model": "opusplan"}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"))
    new_base = {"model": "sonnet"}
    merged2, _ = inst.merge_settings(new_base, merged, manifest, Path("/hooks"))
    assert merged2["model"] == "sonnet"


def test_local_override_survives_base_change():
    base = {"model": "opusplan"}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"))
    merged["model"] = "haiku"  # simulate a hand-edit
    new_base = {"model": "opusplan"}  # base reverts, shouldn't clobber the hand-edit
    merged2, _ = inst.merge_settings(new_base, merged, manifest, Path("/hooks"))
    assert merged2["model"] == "haiku"


def test_local_override_survives_a_third_run_too():
    # Regression test: an earlier version recorded the KEPT value (the
    # override itself) in the manifest instead of what base wanted, so by
    # the 3rd run the override looked "unchanged since we set it" and got
    # silently upgraded away. Must record base's own value every time.
    base = {"model": "opusplan"}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"))
    merged["model"] = "haiku"  # hand-edit
    merged, _ = inst.merge_settings(base, merged, manifest, Path("/hooks"))  # run 2, base unchanged
    assert merged["model"] == "haiku"
    merged, _ = inst.merge_settings(base, merged, manifest, Path("/hooks"))  # run 3
    assert merged["model"] == "haiku", "local override was clobbered on the 3rd run"


def test_removed_base_rule_is_retracted():
    base = {"permissions": {"allow": ["Bash(git status)", "Bash(git show*)"]}}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"))
    assert "Bash(git show*)" in merged["permissions"]["allow"]
    new_base = {"permissions": {"allow": ["Bash(git status)"]}}
    merged2, _ = inst.merge_settings(new_base, merged, manifest, Path("/hooks"))
    assert "Bash(git show*)" not in merged2["permissions"]["allow"]
    assert "Bash(git status)" in merged2["permissions"]["allow"]


def test_user_added_permission_rule_is_never_touched():
    base = {"permissions": {"allow": ["Bash(git status)"]}}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"))
    merged["permissions"]["allow"].append("Bash(npm test)")  # user added this by hand
    new_base = {"permissions": {"allow": []}}
    merged2, _ = inst.merge_settings(new_base, merged, manifest, Path("/hooks"))
    assert "Bash(npm test)" in merged2["permissions"]["allow"]


def test_merge_hooks_finds_block_by_any_matcher_and_updates_in_place():
    settings = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "old-python", "args": ["/old/guard_destructive_commands.py"]}]}
            ]
        }
    }
    entry = inst.merge_hooks(settings, Path("/new/hooks"))
    block = settings["hooks"]["PreToolUse"][0]
    assert block["matcher"] == inst.HOOK_MATCHER
    assert len(block["hooks"]) == 1
    assert block["hooks"][0]["command"] == entry["command"]


def test_merge_statusline_keeps_foreign_statusline():
    settings = {"statusLine": {"type": "command", "command": "my-own-script.sh"}}
    inst.merge_statusline(settings, Path("/hooks"))
    assert settings["statusLine"]["command"] == "my-own-script.sh"
