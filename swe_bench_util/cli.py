"""This module provides the CLI."""

from typing import Optional
import json

import typer

from swe_bench_util import __app_name__, __version__

from datasets import load_dataset

app = typer.Typer()

def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


@app.command()
def get(index:int=0, split: str='dev', dataset_name='princeton-nlp/SWE-bench'):
    dataset = load_dataset(dataset_name, split=split)

    print(json.dumps(dataset[index], indent=2))


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    return