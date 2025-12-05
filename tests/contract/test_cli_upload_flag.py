"""Contract tests for CLI --upload flag integration."""

import re
from typer.testing import CliRunner

from biotoolsllmannotate.cli.main import app

runner = CliRunner()


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_cli_upload_flag_exists():
    """Test that --upload flag is recognized by CLI."""
    result = runner.invoke(app, ["run", "--help"])

    assert result.exit_code == 0
    # Strip ANSI codes and verify --upload appears in help text
    clean_stdout = _strip_ansi(result.stdout)
    assert "--upload" in clean_stdout
    assert "bio.tools" in clean_stdout.lower() or "registry" in clean_stdout.lower()


def test_cli_upload_flag_accepted():
    """Test that --upload flag is accepted without error."""
    # Run with --upload and --help to verify flag parsing works
    result = runner.invoke(app, ["run", "--upload", "--help"])

    # Should not error on the flag itself
    assert result.exit_code == 0
    # Strip ANSI codes and verify no "Error:" or "Invalid" messages
    clean_stdout = _strip_ansi(result.stdout)
    assert "Error:" not in clean_stdout
    assert "Invalid" not in clean_stdout
