import os
from pathlib import Path
from biotoolsllmannotate.io.biotools_api import read_biotools_token


def test_read_biotools_token_present(tmp_path):
    token_file = tmp_path / ".bt_token"
    token_file.write_text("  abc123token\n\n", encoding="utf-8")
    token = read_biotools_token(str(token_file))
    assert token == "abc123token"


def test_read_biotools_token_missing(tmp_path):
    # Provide path that does not exist
    token = read_biotools_token(str(tmp_path / ".bt_token_missing"))
    assert token is None


def test_read_biotools_token_empty(tmp_path):
    token_file = tmp_path / ".bt_token"
    token_file.write_text("   \n\n", encoding="utf-8")
    token = read_biotools_token(str(token_file))
    assert token is None
