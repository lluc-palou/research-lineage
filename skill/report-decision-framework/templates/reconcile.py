#!/usr/bin/env python3
"""Reconcile docs/DECISIONS.md's Commits fields against git history.

Scans commit trailers (`Decision: <ID>`) across the full git history and
compares them against the `**Commits:**` field of each decision entry in
docs/DECISIONS.md. The Commits field is a cache; git trailers are the
canonical record.

Usage:
    python scripts/reconcile.py --check   # report drift, exit 1 if found
    python scripts/reconcile.py --fix     # rewrite Commits fields to match git
"""

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

DECISIONS_PATH = Path("docs/DECISIONS.md")
DECISION_HEADER_RE = re.compile(r"^### (D-\d{8}-[A-Za-z]+-\d+)")
COMMITS_LINE_RE = re.compile(r"^\*\*Commits:\*\* (.*)$")


def get_decision_commits_from_git():
    """Return {decision_id: [(short_hash, author_name), ...]} from trailers."""
    log_format = "%H%x1f%an%x1f%(trailers:key=Decision,valueonly)"
    result = subprocess.run(
        ["git", "log", "--all", f"--format={log_format}"],
        capture_output=True,
        text=True,
        check=True,
    )
    mapping = defaultdict(list)
    for line in result.stdout.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 3:
            continue
        full_hash, author, decision_ids_raw = parts
        decision_ids_raw = decision_ids_raw.strip()
        if not decision_ids_raw:
            continue
        for decision_id in re.split(r"[,\s]+", decision_ids_raw):
            if decision_id:
                mapping[decision_id].append((full_hash[:7], author))
    return mapping


def parse_decisions_file(path):
    """Return (lines, {decision_id: (line_index_of_commits_field, current_value)})."""
    lines = path.read_text().splitlines()
    current_id = None
    commits_fields = {}
    for i, line in enumerate(lines):
        header_match = DECISION_HEADER_RE.match(line)
        if header_match:
            current_id = header_match.group(1)
            continue
        commits_match = COMMITS_LINE_RE.match(line)
        if commits_match and current_id:
            commits_fields[current_id] = (i, commits_match.group(1))
    return lines, commits_fields


def format_commits_value(commit_list):
    if not commit_list:
        return "(none yet)"
    return ", ".join(f"{h} ({a})" for h, a in commit_list)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="report drift only")
    mode.add_argument("--fix", action="store_true", help="rewrite Commits fields")
    args = parser.parse_args()

    if not DECISIONS_PATH.exists():
        print(f"ERROR: {DECISIONS_PATH} not found.", file=sys.stderr)
        sys.exit(2)

    git_commits = get_decision_commits_from_git()
    lines, commits_fields = parse_decisions_file(DECISIONS_PATH)

    drift_found = False

    for decision_id, (line_index, current_value) in commits_fields.items():
        expected_value = format_commits_value(git_commits.get(decision_id, []))
        if current_value.strip() != expected_value.strip():
            drift_found = True
            print(f"DRIFT {decision_id}:")
            print(f"  DECISIONS.md: {current_value}")
            print(f"  git history:  {expected_value}")
            if args.fix:
                lines[line_index] = f"**Commits:** {expected_value}"

    undocumented = set(git_commits) - set(commits_fields)
    for decision_id in sorted(undocumented):
        drift_found = True
        print(
            f"WARNING: {decision_id} referenced in commit trailers but has "
            f"no entry in {DECISIONS_PATH}."
        )

    if args.fix and drift_found:
        DECISIONS_PATH.write_text("\n".join(lines) + "\n")
        print(f"Rewrote {DECISIONS_PATH}.")

    if not drift_found:
        print("No drift found.")
    elif args.check:
        sys.exit(1)


if __name__ == "__main__":
    main()
