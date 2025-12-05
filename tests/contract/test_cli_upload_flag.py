"""Contract tests for CLI --upload flag integration."""

from typer.testing import CliRunner

from biotoolsllmannotate.cli.main import app

runner = CliRunner()


def test_cli_upload_flag_exists():
    """Test that --upload flag is recognized by CLI."""
    result = runner.invoke(app, ["run", "--help"])

    assert result.exit_code == 0
    # Verify --upload appears in help text
    assert "--upload" in result.stdout
    assert "bio.tools" in result.stdout.lower() or "registry" in result.stdout.lower()


def test_cli_upload_flag_accepted():
    """Test that --upload flag is accepted without error."""
    # Run with --upload and --help to verify flag parsing works
    result = runner.invoke(app, ["run", "--upload", "--help"])

    # Should not error on the flag itself
    assert result.exit_code == 0
    # Verify no "Error:" or "Invalid" messages
    assert "Error:" not in result.stdout
    assert "Invalid" not in result.stdout
