#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "docs/release/v0.1-replay-manifest.json"
RELEASE_BRANCH = "release/reconstructed-v0.1"
READY_STATUS = "ready_for_replay"
PB_PATTERNS = [r"\bPB-(?:0[0-9]|10)\b", r"L1-003_PB"]


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, text=True, capture_output=True
    )
    if check and result.returncode:
        raise SystemExit(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0":
        raise SystemExit("unsupported replay manifest schema")
    return payload


def commit_from_sha(sha: str) -> Commit:
    canonical = git("rev-parse", f"{sha}^{{commit}}").strip()
    subject = git("show", "-s", "--format=%s", canonical).strip()
    return Commit(canonical, subject)


def contains_pb_label(text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in PB_PATTERNS)


def validate_manifest(payload: dict[str, Any]) -> dict[str, list[Commit]]:
    base_sha = payload["base"]["sha"]
    canonical_base = git("rev-parse", f"{base_sha}^{{commit}}").strip()
    if canonical_base != base_sha:
        raise SystemExit(f"base SHA is not canonical: {base_sha} -> {canonical_base}")

    seen: set[str] = set()
    groups: dict[str, list[Commit]] = {}
    for version, spec in payload["versions"].items():
        selected: list[Commit] = []
        for sha in spec.get("source_commits", []):
            commit = commit_from_sha(sha)
            if commit.sha in seen:
                raise SystemExit(f"duplicate source commit in manifest: {commit.sha}")
            if contains_pb_label(commit.subject):
                raise SystemExit(
                    f"PB-labelled commit is forbidden in {version}: "
                    f"{commit.sha} {commit.subject}"
                )
            seen.add(commit.sha)
            selected.append(commit)
        groups[version] = selected
    return groups


def verify_clean() -> None:
    if git("status", "--porcelain").strip():
        raise SystemExit("working tree is not clean")


def verify_apply_gate(payload: dict[str, Any], groups: dict[str, list[Commit]]) -> None:
    for version, spec in payload["versions"].items():
        status = spec.get("status")
        if status != READY_STATUS:
            raise SystemExit(
                f"apply blocked: {version} status is {status!r}; "
                f"expected {READY_STATUS!r}"
            )
        if not groups[version]:
            raise SystemExit(f"apply blocked: {version} has no frozen source commits")


def apply(payload: dict[str, Any], groups: dict[str, list[Commit]]) -> None:
    verify_apply_gate(payload, groups)
    verify_clean()

    current_branch = git("branch", "--show-current").strip()
    if current_branch != RELEASE_BRANCH:
        raise SystemExit(f"apply requires branch {RELEASE_BRANCH}, got {current_branch!r}")

    base_sha = payload["base"]["sha"]
    head = git("rev-parse", "HEAD").strip()
    if head != base_sha:
        raise SystemExit(
            "apply starts only from the frozen v0.1.0 base. "
            f"expected {base_sha}, got {head}"
        )

    for version, commits in groups.items():
        for commit in commits:
            subprocess.run(
                ["git", "cherry-pick", "--no-commit", commit.sha],
                cwd=REPO_ROOT,
                check=True,
            )
        git(
            "commit",
            "-m",
            f"Reconstruct {version} from frozen source manifest",
            "-m",
            "Source-of-truth historical commits are preserved unchanged; "
            "this checkpoint only creates the cumulative release lineage.",
        )
        print(f"{version}: {git('rev-parse', 'HEAD').strip()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--manifest",
        default=str(MANIFEST_PATH.relative_to(REPO_ROOT)),
        help="frozen replay manifest relative to repository root",
    )
    args = parser.parse_args()

    manifest_path = REPO_ROOT / args.manifest
    payload = load_manifest(manifest_path)
    groups = validate_manifest(payload)

    print(f"base {payload['base']['version']}: {payload['base']['sha']}")
    for version, commits in groups.items():
        status = payload["versions"][version]["status"]
        print(f"[{version}] status={status} commits={len(commits)}")
        for commit in commits:
            print(f"  {commit.sha}  {commit.subject}")

    if args.apply:
        apply(payload, groups)
    else:
        blocked = [
            version
            for version, spec in payload["versions"].items()
            if spec.get("status") != READY_STATUS
        ]
        if blocked:
            print("dry-run validated; apply remains blocked by: " + ", ".join(blocked))
        else:
            print("dry-run validated; manifest is eligible for --apply")


if __name__ == "__main__":
    main()
