from typer.testing import CliRunner
from swe_bench_util import cli

runner = CliRunner()

def test_create_cli():
    result = runner.invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout
