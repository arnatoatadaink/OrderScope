#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TOOLS_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = TOOLS_ROOT / "docs/release/v0.1-replay-manifest.json"
RELEASE_BRANCH = "release/reconstructed-v0.1"
READY_STATUS = "ready_for_replay"
PB_PATTERNS = [r"\bPB-(?:0[0-9]|10)\b", r"L1-003_PB"]


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


def git(root: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True
    )
    if check and result.returncode:
        raise SystemExit(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0":
        raise SystemExit("unsupported replay manifest schema")
    return payload


def commit_from_sha(root: Path, sha: str) -> Commit:
    canonical = git(root, "rev-parse", f"{sha}^{{commit}}").strip()
    subject = git(root, "show", "-s", "--format=%s", canonical).strip()
    return Commit(canonical, subject)


def contains_pb_label(text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in PB_PATTERNS)


def repo_identity(root: Path) -> tuple[str, str]:
    common_dir = git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
    top = git(root, "rev-parse", "--show-toplevel").strip()
    return str(Path(common_dir).resolve()), str(Path(top).resolve())


def verify_same_repository(source_root: Path, target_root: Path) -> None:
    source_common, _ = repo_identity(source_root)
    target_common, _ = repo_identity(target_root)
    if source_common != target_common:
        raise SystemExit(
            "target worktree does not share the same Git common directory as the tooling checkout: "
            f"source={source_common} target={target_common}"
        )


def validate_manifest(
    git_root: Path, payload: dict[str, Any]
) -> dict[str, list[Commit]]:
    base_sha = payload["base"]["sha"]
    canonical_base = git(git_root, "rev-parse", f"{base_sha}^{{commit}}").strip()
    if canonical_base != base_sha:
        raise SystemExit(f"base SHA is not canonical: {base_sha} -> {canonical_base}")

    seen: set[str] = set()
    groups: dict[str, list[Commit]] = {}
    for version, spec in payload["versions"].items():
        selected: list[Commit] = []
        for sha in spec.get("source_commits", []):
            commit = commit_from_sha(git_root, sha)
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


def verify_clean(root: Path) -> None:
    if git(root, "status", "--porcelain").strip():
        raise SystemExit(f"working tree is not clean: {root}")


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


def abort_cherry_pick_if_needed(root: Path) -> None:
    cherry_pick_head = git(root, "rev-parse", "-q", "--verify", "CHERRY_PICK_HEAD", check=False).strip()
    if cherry_pick_head:
        subprocess.run(["git", "cherry-pick", "--abort"], cwd=root, check=False)


def apply(
    target_root: Path,
    payload: dict[str, Any],
    groups: dict[str, list[Commit]],
) -> None:
    verify_apply_gate(payload, groups)
    verify_clean(target_root)

    current_branch = git(target_root, "branch", "--show-current").strip()
    if current_branch != RELEASE_BRANCH:
        raise SystemExit(
            f"apply requires branch {RELEASE_BRANCH}, got {current_branch!r} in {target_root}"
        )

    base_sha = payload["base"]["sha"]
    head = git(target_root, "rev-parse", "HEAD").strip()
    if head != base_sha:
        raise SystemExit(
            "apply starts only from the frozen v0.1.0 base. "
            f"expected {base_sha}, got {head}"
        )

    for version, commits in groups.items():
        try:
            for commit in commits:
                subprocess.run(
                    ["git", "cherry-pick", "--no-commit", commit.sha],
                    cwd=target_root,
                    check=True,
                )
            git(
                target_root,
                "commit",
                "-m",
                f"Reconstruct {version} from frozen source manifest",
                "-m",
                "Source-of-truth historical commits are preserved unchanged; "
                "this checkpoint only creates the cumulative release lineage.",
            )
        except subprocess.CalledProcessError as error:
            abort_cherry_pick_if_needed(target_root)
            raise SystemExit(
                f"replay stopped during {version}; target worktree was left for manual inspection. "
                f"failed command: {' '.join(error.cmd)}"
            ) from error
        print(f"{version}: {git(target_root, 'rev-parse', 'HEAD').strip()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--manifest",
        default=str(MANIFEST_PATH.relative_to(TOOLS_ROOT)),
        help="frozen replay manifest relative to tooling checkout",
    )
    parser.add_argument(
        "--target-worktree",
        type=Path,
        help=(
            "separate worktree checked out on release/reconstructed-v0.1; "
            "required for --apply"
        ),
    )
    args = parser.parse_args()

    manifest_path = TOOLS_ROOT / args.manifest
    payload = load_manifest(manifest_path)

    git_root = TOOLS_ROOT
    target_root: Path | None = None
    if args.target_worktree is not None:
        target_root = args.target_worktree.expanduser().resolve()
        if not target_root.exists():
            raise SystemExit(f"target worktree does not exist: {target_root}")
        verify_same_repository(TOOLS_ROOT, target_root)
        git_root = target_root

    groups = validate_manifest(git_root, payload)

    print(f"base {payload['base']['version']}: {payload['base']['sha']}")
    for version, commits in groups.items():
        status = payload["versions"][version]["status"]
        print(f"[{version}] status={status} commits={len(commits)}")
        for commit in commits:
            print(f"  {commit.sha}  {commit.subject}")

    if args.apply:
        if target_root is None:
            raise SystemExit("--apply requires --target-worktree")
        apply(target_root, payload, groups)
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
