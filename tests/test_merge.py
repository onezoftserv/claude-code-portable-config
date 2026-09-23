import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import install as inst  # noqa: E402


def fresh_manifest():
    return {"files": {}, "permission_rules": {}}


def test_first_run_adopts_base_values():
    base = {"model": "opusplan", "permissions": {"allow": ["Bash(git status)"]}}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"), {})
    assert merged["model"] == "opusplan"
    assert "Bash(git status)" in merged["permissions"]["allow"]


def test_rerun_with_unchanged_base_is_idempotent():
    base = {"model": "opusplan", "permissions": {"allow": ["Bash(git status)"]}}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"), {})
    merged2, _ = inst.merge_settings(base, merged, manifest, Path("/hooks"), {})
    assert merged == merged2


def test_base_change_propagates_on_rerun():
    base = {"model": "opusplan"}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"), {})
    new_base = {"model": "sonnet"}
    merged2, _ = inst.merge_settings(new_base, merged, manifest, Path("/hooks"), {})
    assert merged2["model"] == "sonnet"


def test_local_override_wins_over_base_and_survives_repeated_runs():
    base = {"model": "opusplan"}
    local = {"model": "haiku"}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"), local)
    assert merged["model"] == "haiku"
    # base changing shouldn't matter -- local always wins for a managed key
    for _ in range(3):
        merged, _ = inst.merge_settings({"model": "sonnet"}, merged, manifest, Path("/hooks"), local)
        assert merged["model"] == "haiku"


def test_hand_editing_target_directly_does_not_survive_a_managed_key():
    # Intentional: install.py fully owns managed scalar keys now. A local
    # override must go through settings.local.json, not a hand-edit of the
    # installed settings.json -- that gets overwritten on the next run.
    base = {"model": "opusplan"}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"), {})
    merged["model"] = "haiku"  # hand-edit, not via settings.local.json
    merged2, _ = inst.merge_settings(base, merged, manifest, Path("/hooks"), {})
    assert merged2["model"] == "opusplan"


def test_removed_base_rule_is_retracted():
    base = {"permissions": {"allow": ["Bash(git status)", "Bash(git show*)"]}}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"), {})
    assert "Bash(git show*)" in merged["permissions"]["allow"]
    new_base = {"permissions": {"allow": ["Bash(git status)"]}}
    merged2, _ = inst.merge_settings(new_base, merged, manifest, Path("/hooks"), {})
    assert "Bash(git show*)" not in merged2["permissions"]["allow"]
    assert "Bash(git status)" in merged2["permissions"]["allow"]


def test_user_added_permission_rule_is_never_touched():
    base = {"permissions": {"allow": ["Bash(git status)"]}}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"), {})
    merged["permissions"]["allow"].append("Bash(npm test)")  # user added this by hand
    new_base = {"permissions": {"allow": []}}
    merged2, _ = inst.merge_settings(new_base, merged, manifest, Path("/hooks"), {})
    assert "Bash(npm test)" in merged2["permissions"]["allow"]


def test_local_permissions_are_unioned_in():
    base = {"permissions": {"allow": ["Bash(git status)"]}}
    local = {"permissions": {"allow": ["Bash(npm test)"]}}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"), local)
    assert set(merged["permissions"]["allow"]) == {"Bash(git status)", "Bash(npm test)"}


def test_local_remove_retracts_a_base_rule_even_from_a_different_list():
    # allow/ask/deny have their own precedence in Claude Code (deny > ask >
    # allow), so a rule can't be "overridden" by adding it to a higher-
    # precedence list -- `remove` deletes it outright instead.
    base = {"permissions": {"ask": ["Bash(rm -rf*)"]}}
    local = {"permissions": {"remove": {"ask": ["Bash(rm -rf*)"]}}}
    manifest = fresh_manifest()
    merged, _ = inst.merge_settings(base, {}, manifest, Path("/hooks"), local)
    assert "Bash(rm -rf*)" not in merged.get("permissions", {}).get("ask", [])


def test_local_json_ignores_unrecognized_top_level_keys(tmp_path, monkeypatch):
    (tmp_path / "settings.local.json").write_text(
        '{"model": "haiku", "_comment": "not a real key", "theme": "dark"}', encoding="utf-8"
    )
    monkeypatch.setattr(inst, "REPO_ROOT", tmp_path)
    local = inst.load_local_overrides()
    assert local == {"model": "haiku"}


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
