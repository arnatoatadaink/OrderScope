"""Application-owned CLI for the local OrderScope runtime."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path

import typer
import uvicorn

from orderscope_local.config import load_local_config
from orderscope_local.contracts import ContractViolation
from orderscope_local.integration import run_scheduler
from orderscope_local.integration.operator import (
    inspect_retention,
    load_operator_snapshot,
    plan_bounded_replay,
    select_due_deletions,
)
from orderscope_local.local_api.health import LOCALHOST_BIND_HOST, LocalServerBinding
from orderscope_local.local_api.read_api import LocalReadSnapshot, create_read_app
from orderscope_local.news import (
    AlpacaNewsHttpTransport,
    collect_news_recall_candidates,
    load_news_recall_benchmark,
    render_news_recall_markdown,
    write_news_recall_candidates,
)
from orderscope_local.news.recall_labeling import finalize_benchmark, write_label_template


app = typer.Typer(help="OrderScope local analysis CLI", no_args_is_help=True)
import_app = typer.Typer(help="Local import operations", no_args_is_help=True)
quality_app = typer.Typer(help="Local quality operations", no_args_is_help=True)
schedule_app = typer.Typer(help="Local scheduler operations", no_args_is_help=True)
operator_app = typer.Typer(help="Bounded operator retention/replay planning", no_args_is_help=True)
app.add_typer(import_app, name="import")
app.add_typer(quality_app, name="quality")
app.add_typer(schedule_app, name="schedule")
app.add_typer(operator_app, name="operator")


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


@quality_app.command("news-recall")
def quality_news_recall(
    benchmark: Path = typer.Option(..., exists=True, dir_okay=False, readable=True, help="Validated N1-006 benchmark JSON file."),
) -> None:
    """Evaluate one explicit SEC/IR-to-News recall benchmark and print Markdown."""

    dataset = load_news_recall_benchmark(benchmark)
    typer.echo(render_news_recall_markdown(benchmark=dataset), nl=False)


@quality_app.command("news-recall-candidates")
def quality_news_recall_candidates(
    start: str = typer.Option(..., help="30-93 day retrospective window start, ISO-8601 UTC."),
    end: str = typer.Option(..., help="Retrospective window end, ISO-8601 UTC."),
    filename: str = typer.Option("amd-nvda-news-candidates.json", help="Simple JSON filename beneath data_root/benchmarks/n1-006."),
    max_pages_per_symbol: int = typer.Option(100, min=1, max=500),
) -> None:
    """Fetch metadata-only AMD/NVDA Alpaca News candidates for manual benchmark labeling."""

    window_start = _utc_timestamp(start, "start")
    window_end = _utc_timestamp(end, "end")
    config = load_local_config(os.environ)
    transport = AlpacaNewsHttpTransport(environ=os.environ)
    candidates = collect_news_recall_candidates(
        transport=transport,
        window_start=window_start,
        window_end=window_end,
        max_pages_per_symbol=max_pages_per_symbol,
    )
    destination = write_news_recall_candidates(
        data_root=config.data_root,
        filename=filename,
        window_start=window_start,
        window_end=window_end,
        candidates=candidates,
    )
    typer.echo(f"candidate_count={len(candidates)} output={destination}")


@quality_app.command("news-recall-label-template")
def quality_news_recall_label_template(
    candidates: Path = typer.Option(..., exists=True, dir_okay=False, readable=True),
    filename: str = typer.Option("amd-nvda-news-labels.json"),
) -> None:
    """Create an explicit review template for every acquired News candidate."""

    config = load_local_config(os.environ)
    destination = write_label_template(
        data_root=config.data_root,
        filename=filename,
        candidate_path=candidates,
    )
    typer.echo(f"label_template={destination}")


@quality_app.command("news-recall-finalize")
def quality_news_recall_finalize(
    references: Path = typer.Option(..., exists=True, dir_okay=False, readable=True),
    candidates: Path = typer.Option(..., exists=True, dir_okay=False, readable=True),
    labels: Path = typer.Option(..., exists=True, dir_okay=False, readable=True),
    filename: str = typer.Option("amd-nvda-news-benchmark-final.json"),
) -> None:
    """Finalize a fully reviewed candidate set into the N1-006 benchmark schema."""

    config = load_local_config(os.environ)
    if Path(filename).name != filename or not filename.endswith(".json"):
        raise ContractViolation("filename must be a simple .json filename")
    destination = config.data_root / "benchmarks" / "n1-006" / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    benchmark = finalize_benchmark(
        reference_path=references,
        candidate_path=candidates,
        label_path=labels,
        output_path=destination,
    )
    typer.echo(
        f"references={len(benchmark.references)} discoveries={len(benchmark.discoveries)} "
        f"unresolved={len(benchmark.unresolved_labels)} output={destination}"
    )


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


@operator_app.command("inspect")
def operator_inspect(
    snapshot: Path = typer.Option(..., exists=True, dir_okay=False, readable=True),
    now: str | None = typer.Option(None, help="Inspection instant as ISO-8601 UTC; defaults to current UTC."),
) -> None:
    """Inspect bounded retention/retry metadata without reading raw bodies."""

    loaded = load_operator_snapshot(snapshot)
    instant = _utc_timestamp(now, "now") if now is not None else datetime.now(timezone.utc)
    retention = inspect_retention(snapshot=loaded, now=instant)
    retryable = sum(1 for item in loaded.replay if item.state.value in {"RETRYABLE", "FAILED"})
    typer.echo(
        f"retention_pending={retention.pending} due={retention.due} overdue={retention.overdue} "
        f"retention_failed={retention.retryable_or_failed} replay_retryable={retryable} deleted={retention.deleted}"
    )


@operator_app.command("replay-plan")
def operator_replay_plan(
    snapshot: Path = typer.Option(..., exists=True, dir_okay=False, readable=True),
    source: str = typer.Option(...),
    start: str = typer.Option(..., help="Explicit replay window start, ISO-8601 UTC."),
    end: str = typer.Option(..., help="Explicit replay window end, ISO-8601 UTC."),
    max_items: int = typer.Option(10, min=1, max=100),
) -> None:
    """Dry-run one explicit bounded replay selection; this command never executes provider work."""

    loaded = load_operator_snapshot(snapshot)
    plan = plan_bounded_replay(
        snapshot=loaded,
        source=source,
        start=_utc_timestamp(start, "start"),
        end=_utc_timestamp(end, "end"),
        max_items=max_items,
        dry_run=True,
    )
    typer.echo(f"source={plan.source} selected={len(plan.work_ids)} dry_run=true work_ids={','.join(plan.work_ids)}")


@operator_app.command("delete-plan")
def operator_delete_plan(
    snapshot: Path = typer.Option(..., exists=True, dir_okay=False, readable=True),
    content_ref: list[str] = typer.Option(..., "--content-ref", help="Explicit due content ref; repeat option for multiple refs."),
    now: str | None = typer.Option(None, help="Selection instant as ISO-8601 UTC; defaults to current UTC."),
    max_items: int = typer.Option(10, min=1, max=100),
) -> None:
    """Dry-run explicitly selected due deletions; no storage mutation occurs."""

    loaded = load_operator_snapshot(snapshot)
    instant = _utc_timestamp(now, "now") if now is not None else datetime.now(timezone.utc)
    selected = select_due_deletions(snapshot=loaded, now=instant, content_refs=content_ref, max_items=max_items)
    typer.echo(f"selected={len(selected)} dry_run=true content_refs={','.join(item.content_ref for item in selected)}")


def _utc_timestamp(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise ContractViolation(f"{field} must be ISO-8601 UTC") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
    return parsed


if __name__ == "__main__":
    app()
