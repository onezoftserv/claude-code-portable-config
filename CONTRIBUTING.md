# Contributing

This is a personal Claude Code config, published so it's easy to install and so others can borrow from it. PRs and issues are welcome, but changes get merged based on whether they fit this specific setup, not on general "is this a good idea in the abstract."

## Before opening a PR

- **Run the tests**: `pip install pytest jsonschema && pytest -v` from the repo root. CI runs the same suite on ubuntu/macos/windows × Python 3.10/3.12, plus a job that runs `install.sh`/`install.ps1` themselves.
- **Checking coverage locally?** Install the exact pinned versions CI uses (`pip install "pytest-cov==7.1.0" "coverage==7.16.1"`), not whatever's already on your machine. Different `coverage` major versions disagree, sometimes wildly, on whether a `subprocess.run()` e2e test (which is most of `test_install_e2e.py`) counts as covering the code it ran — an older `coverage` here showed 92% on `scripts/install.py` where the pinned version (and Codecov) correctly shows 57%, with the exact same tests and code.
- **Test on the OS you're changing.** If you touch `install.ps1`, actually run it on Windows (or in CI) — don't assume bash-tested logic translates.
- **No new runtime dependencies for `scripts/install.py`** or the hooks. They're stdlib-only Python on purpose, since they run on whatever interpreter happens to be on a given machine. `jsonschema` is a test-only dependency.
- **Follow the existing patterns**: exec-form `args` for hooks (no shell), the manifest-based upgrade tracking in `scripts/install.py` for anything that needs "safe to overwrite vs. hand-edited" logic, `settings.local.json` for anything machine-specific rather than a new config file.

## Adding a hook

Put the script in `hooks/common/`, wire it into `scripts/install.py`'s hook-merging logic (or add a new merge function if it's not a `PreToolUse` guard), and add test cases to `tests/`. Keep it pure-stdlib and cheap — the guard hook runs on every matching tool call, so a slow or LLM-backed hook (`type: "prompt"`/`"agent"`) defeats the token-efficiency point of this repo unless there's a specific reason for it. If you do add one of those, set `model` explicitly — both types default to Haiku/a small model when it's unset.

## Adding an OS-specific behavior

Everything here is OS-agnostic Python on purpose. Don't add OS branching unless you've hit a real platform difference — most "portability" problems here turned out to have a single cross-platform answer instead of one: `sys.executable` + exec-form `args` instead of guessing `python` vs `python3` vs `py`, `shutil.which("bash")` instead of assuming a shell. If you genuinely need OS-specific behavior (clipboard, notifications, path separators), put the script in `hooks/common/` like everything else and branch on `platform.system()` inside it — there's no separate `hooks/windows/`-style directory; one existed early on, held nothing but READMEs, and was removed.

## Commit style

Explain *why*, not just what — see `git log` for the tone. Reference what broke or what a review found when that's the reason for the change, not just what the diff does.

## Releases

Tags follow semver (`vX.Y.Z`). `CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) — add an entry under `## [Unreleased]` (create that section if it's missing) as part of your PR, not as a separate step later.
