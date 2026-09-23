import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks" / "common"))
from guard_destructive_commands import is_dangerous  # noqa: E402

CASES = [
    ("ls -la", False),
    ("rm -rf /", True),
    ("rm -fr /", True),
    ("rm -r -f /", True),
    ("rm -rf ~", True),
    ("rm -rf *", True),
    ("rm -rf node_modules", True),
    ("git push origin main", False),
    ("git push origin main --force", True),
    ("git push -f origin main", True),
    ("git push --force-with-lease origin main", False),
    ("git push --force-with-lease --force origin main", True),
    ("git push origin +main", True),
    ("git push --delete origin main", True),
    ("git push origin :main", True),
    ("git reset --hard HEAD~1", True),
    ("git clean -fd", True),
    ("git clean --force", True),
    ("git checkout -- .", True),
    ("git restore .", True),
    ("git branch -D old-feature", True),
    ('grep -rn "drop table" .', False),
    ('npm test -- --grep "DROP TABLE"', False),
    ('git commit -m "fix: git reset --hard bug"', False),
    (r"Remove-Item -Recurse -Force C:\temp\x", True),
    (r"Remove-Item -r -fo C:\temp\x", True),
    (r"rd /s /q C:\temp\x", True),
    ("DROP TABLE users;", True),
]


@pytest.mark.parametrize("command,expected", CASES)
def test_is_dangerous(command, expected):
    assert bool(is_dangerous(command)) == expected, f"is_dangerous({command!r}) reason={is_dangerous(command)!r}"


def test_empty_and_none_command_do_not_crash():
    assert is_dangerous("") == ""
    assert is_dangerous(None) == ""
