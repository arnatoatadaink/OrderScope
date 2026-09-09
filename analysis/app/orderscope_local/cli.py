"""Application-owned CLI for the local OrderScope runtime."""

from __future__ import annotations

import os

import typer
import uvicorn

from orderscope_local.config import load_local_config
from orderscope_local.local_api.health import LOCALHOST_BIND_HOST, LocalServerBinding
from orderscope_local.local_api.read_api import LocalReadSnapshot, create_read_app


app = typer.Typer(help="OrderScope local analysis CLI", no_args_is_help=True)
import_app = typer.Typer(help="Local import operations", no_args_is_help=True)
quality_app = typer.Typer(help="Local quality operations", no_args_is_help=True)
app.add_typer(import_app, name="import")
app.add_typer(quality_app, name="quality")


@app.command()
def serve(
    port: int = typer.Option(8000, min=1, max=65535, help="Loopback TCP port."),
) -> None:
    """Start the accepted read-only API on literal IPv4 loopback only."""

    config = load_local_config(os.environ)
    binding = LocalServerBinding(host=LOCALHOST_BIND_HOST)
    read_app = create_read_app(snapshot=LocalReadSnapshot(), binding=binding)
    uvicorn.run(
        read_app,
        host=binding.host,
        port=port,
        log_level=config.log_level.lower(),
    )


@import_app.command("status")
def import_status() -> None:
    """Show the v0.1 import execution boundary without starting a job."""

    typer.echo("import operations are CLI-only; explicit import commands are added by their owning tasks")


@quality_app.command("status")
def quality_status() -> None:
    """Show the v0.1 quality execution boundary without starting a job."""

    typer.echo("quality operations are CLI-only; explicit quality commands are added by their owning tasks")


if __name__ == "__main__":
    app()
