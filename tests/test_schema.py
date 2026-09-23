import json
import subprocess
import sys
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

REPO_ROOT = Path(__file__).resolve().parent.parent
# Vendored (not fetched at test time -- a network call is the flakiest thing
# a test suite can do) from https://www.schemastore.org/claude-code-settings.json
# on 2026-09-23, at commit c27e15c. Schema is `additionalProperties: true`, so
# it only catches type errors, not typo'd/unrecognized keys -- and it can lag
# behind newly added settings.json keys. Refresh manually with:
#   curl -fsSL https://www.schemastore.org/claude-code-settings.json -o tests/claude-code-settings.schema.json
SCHEMA_PATH = Path(__file__).resolve().parent / "claude-code-settings.schema.json"


@pytest.fixture(scope="module")
def schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_settings_base_matches_schema(schema):
    base = json.loads((REPO_ROOT / "settings.base.json").read_text(encoding="utf-8"))
    jsonschema.validate(base, schema)


def test_installed_settings_matches_schema(tmp_path, schema):
    # Validate what actually ships to a machine, not just the base file.
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "install.py"), "--target", str(tmp_path)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    installed = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    jsonschema.validate(installed, schema)
