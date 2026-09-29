#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = "99b08a0b5fa1bec5921dc42e630c579a4e83c401"
RELEASE_BRANCH = "release/reconstructed-v0.1"

VERSION_PATTERNS = {
    "v0.1.1": [
        r"\bUWBS-00[1-4]\b",
        r"\bUWBS-016\b",
        r"\bUWBS-02[3-6]\b",
        r"\bR0-00[1-9]\b",
        r"\bW1-001\b",
    ],
    "v0.1.2": [r"\bUWBS-01[1-5]\b", r"\bA0-00[3-7]\b"],
    "v0.1.3": [
        r"\bUWBS-02[7-9]\b",
        r"\bUWBS-03[0-6]\b",
        r"\bA0-00[89]\b",
        r"\bA0-01[0-7]\b",
    ],
}

EXCLUDE_PATTERNS = [
    r"\bPB-(?:0[0-9]|10)\b",
    r"L1-003_PB",
]

@dataclass(frozen=True)
class Commit:
    sha: str
    parents: tuple[str, ...]
    subject: str


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, text=True, capture_output=True
    )
    if check and result.returncode:
        raise SystemExit(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def all_commits() -> list[Commit]:
    raw = git(
        "log",
        "--all",
        "--topo-order",
        "--reverse",
        "--format=%H%x09%P%x09%s",
    )
    commits: list[Commit] = []
    for line in raw.splitlines():
        sha, parents, subject = line.split("\t", 2)
        commits.append(Commit(sha, tuple(parents.split()) if parents else (), subject))
    return commits


def matches(subject: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, subject, re.IGNORECASE) for pattern in patterns)


def classify(commits: list[Commit]) -> dict[str, list[Commit]]:
    result: dict[str, list[Commit]] = {version: [] for version in VERSION_PATTERNS}
    for commit in commits:
        if any(re.search(p, commit.subject, re.IGNORECASE) for p in EXCLUDE_PATTERNS):
            continue
        hits = [
            version
            for version, patterns in VERSION_PATTERNS.items()
            if matches(commit.subject, patterns)
        ]
        if len(hits) > 1:
            raise SystemExit(
                f"ambiguous commit {commit.sha}: {commit.subject!r} -> {hits}"
            )
        if hits:
            result[hits[0]].append(commit)
    return result


def write_plan(groups: dict[str, list[Commit]], path: Path) -> None:
    payload = {
        "base_sha": BASE_SHA,
        "release_branch": RELEASE_BRANCH,
        "versions": {
            version: [
                {"sha": commit.sha, "subject": commit.subject}
                for commit in commits
            ]
            for version, commits in groups.items()
        },
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def verify_clean() -> None:
    if git("status", "--porcelain").strip():
        raise SystemExit("working tree is not clean")


def apply(groups: dict[str, list[Commit]]) -> None:
    verify_clean()
    current_branch = git("branch", "--show-current").strip()
    if current_branch != RELEASE_BRANCH:
        raise SystemExit(f"apply requires branch {RELEASE_BRANCH}, got {current_branch!r}")
    head = git("rev-parse", "HEAD").strip()
    if head != BASE_SHA:
        raise SystemExit(
            "apply starts only from the frozen v0.1.0 base. "
            f"expected {BASE_SHA}, got {head}"
        )

    for version, commits in groups.items():
        if not commits:
            raise SystemExit(f"no source commits selected for {version}")
        for commit in commits:
            # Reapply changes without preserving historical commit topology.
            # Conflicts intentionally stop the reconstruction for manual review.
            subprocess.run(
                ["git", "cherry-pick", "--no-commit", commit.sha],
                cwd=REPO_ROOT,
                check=True,
            )
        git("commit", "-m", f"Reconstruct {version} from accepted source history")
        print(f"{version}: {git('rev-parse', 'HEAD').strip()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="apply replay to the release branch")
    parser.add_argument(
        "--plan",
        default="var/release/v0.1-reconstruction-plan.json",
        help="write the discovered source-commit plan here",
    )
    args = parser.parse_args()

    commits = all_commits()
    groups = classify(commits)
    plan_path = REPO_ROOT / args.plan
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    write_plan(groups, plan_path)

    for version, selected in groups.items():
        print(f"[{version}] {len(selected)} source commits")
        for commit in selected:
            print(f"  {commit.sha}  {commit.subject}")

    if args.apply:
        apply(groups)
    else:
        print(f"dry-run only; plan written to {plan_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
