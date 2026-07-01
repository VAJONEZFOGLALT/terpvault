from typer.testing import CliRunner
from terpvault.cli import app

runner = CliRunner()


def test_help_shows_sync():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "sync" in result.output


def test_sync_unknown_supplier_errors():
    result = runner.invoke(app, ["sync", "nonexistent-supplier"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_sync_command_in_help():
    result = runner.invoke(app, ["sync", "--help"])
    assert result.exit_code == 0
    assert "supplier" in result.output
