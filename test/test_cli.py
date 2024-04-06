from typer.testing import CliRunner
from swe_bench_util import cli

runner = CliRunner()


def test_create_cli():
    result = runner.invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout


def test_assistants():
    #result = runner.invoke(cli.app, ["index","astra-assistants","--dataset-name", "princeton-nlp/SWE-bench","--id", "sqlfluff__sqlfluff-4764", "--max", "10000"])
    #result = runner.invoke(cli.app, ["index","astra-assistants","--dataset-name", "princeton-nlp/SWE-bench", "--max", "10000", "--split","test"])
    # result = runner.invoke(cli.app, ["index","astra-assistants","--dataset-name", "princeton-nlp/SWE-bench","--id", "astropy__astropy-11693", "--max", "10000", "--split", "test"])
    # assert  result.exit_code == 0
    pass