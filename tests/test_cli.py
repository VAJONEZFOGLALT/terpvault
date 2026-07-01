from typer.testing import CliRunner
from terpvault.cli import app

runner = CliRunner()


def test_help_shows_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "sync" in result.output
    assert "diff" in result.output
    assert "changes" in result.output


def test_help_diff():
    result = runner.invoke(app, ["diff", "--help"])
    assert result.exit_code == 0
    assert "supplier" in result.output


def test_help_changes():
    result = runner.invoke(app, ["changes", "--help"])
    assert result.exit_code == 0
    assert "latest" in result.output
    assert "snapshot-a" in result.output
    assert "snapshot-b" in result.output


def test_sync_unknown_supplier_errors():
    result = runner.invoke(app, ["sync", "nonexistent-supplier"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_diff_no_changes():
    result = runner.invoke(app, ["diff", "terpenes-uk"])
    assert result.exit_code == 0


def test_changes_no_such_supplier():
    result = runner.invoke(app, ["changes", "nonexistent"])
    assert result.exit_code == 0


def test_changes_snapshot_invalid_id():
    result = runner.invoke(app, ["changes", "terpenes-uk", "--snapshot-a", "abc", "--snapshot-b", "xyz"])
    assert result.exit_code != 0
    assert "Snapshot not found" in result.output


def test_changes_snapshot_missing_b():
    result = runner.invoke(app, ["changes", "terpenes-uk", "--snapshot-a", "abc"])
    assert result.exit_code != 0
    assert "snapshot-b" in result.output


def test_changes_latest_no_data():
    result = runner.invoke(app, ["changes", "terpenes-uk", "--latest"])
    assert result.exit_code == 0
    assert "No changes" in result.output
