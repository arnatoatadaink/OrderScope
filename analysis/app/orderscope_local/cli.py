"""Application-owned CLI for the local OrderScope runtime."""

from __future__ import annotations

import os

import typer
import uvicorn

from orderscope_local.config import load_local_config
from orderscope_local.integration import run_scheduler
from orderscope_local.local_api.health import LOCALHOST_BIND_HOST, LocalServerBinding
from orderscope_local.local_api.read_api import LocalReadSnapshot, create_read_app


app = typer.Typer(help="OrderScope local analysis CLI", no_args_is_help=True)
import_app = typer.Typer(help="Local import operations", no_args_is_help=True)
quality_app = typer.Typer(help="Local quality operations", no_args_is_help=True)
schedule_app = typer.Typer(help="Local scheduler operations", no_args_is_help=True)
app.add_typer(import_app, name="import")
app.add_typer(quality_app, name="quality")
app.add_typer(schedule_app, name="schedule")


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


@schedule_app.command("run")
def schedule_run(
    max_jobs: int = typer.Option(10, min=1, max=100, help="Maximum jobs to execute in this bounded run."),
    resume_after: str | None = typer.Option(None, help="Resume after a completed scheduler job name."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show the bounded selection without executing jobs."),
) -> None:
    """Manually start one bounded local scheduler cycle."""

    config = load_local_config(os.environ)
    result = run_scheduler(
        jobs=(),
        lock_path=config.data_root / "locks" / "scheduler.lock",
        max_jobs=max_jobs,
        resume_after=resume_after,
        dry_run=dry_run,
    )
    typer.echo(
        f"selected={len(result.selected)} completed={len(result.completed)} dry_run={str(result.dry_run).lower()}"
    )


if __name__ == "__main__":
    app()
