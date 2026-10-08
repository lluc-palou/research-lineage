#!/usr/bin/env python3
"""
Research Lineage Reconciliation

Reconciles the `**Commits:**` field of every entry in docs/DECISIONS.md against the `Decision:`
trailers found across the full git history (`git log --all`), which are the canonical record, and
validates that every block ID cited in `Concept:` trailers or in `**Linked to:**` fields exists as a
`{#ID}` anchor in docs/REPORT.md. The Commits field is treated as a cache: it must always be a subset
of what the trailers show, and `--fix` rewrites it to match them exactly, idempotently.

Usage:
    python scripts/reconcile.py --check   # report drift, exit 1 if any is found (pre-push safe)
    python scripts/reconcile.py --fix     # rewrite stale Commits fields, then report what remains
"""

import re
import sys
import argparse
import subprocess
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Project-relative artifact locations
DECISIONS_RELATIVE_PATH = Path("docs/DECISIONS.md")
REPORT_RELATIVE_PATH = Path("docs/REPORT.md")

# ID grammar (SPEC.md section 5)
DECISION_ID_PATTERN = r"D-\d{8}-[A-Za-z]+-\d+"
BLOCK_ID_PATTERN = r"[CIE]\d+"
DECISION_ID_RE = re.compile(rf"^{DECISION_ID_PATTERN}$")
BLOCK_ID_RE = re.compile(rf"^{BLOCK_ID_PATTERN}$")

# DECISIONS.md / REPORT.md line patterns
DECISION_HEADER_RE = re.compile(rf"^### ({DECISION_ID_PATTERN})\b")
COMMITS_LINE_RE = re.compile(r"^\*\*Commits:\*\*\s*(.*)$")
LINKED_TO_LINE_RE = re.compile(r"^\*\*Linked to:\*\*\s*(.*)$")
COMMIT_ENTRY_RE = re.compile(r"\b([0-9a-fA-F]{7,40})\b(?:\s*\(([^)]*)\))?")
REPORT_ANCHOR_RE = re.compile(rf"\{{#({BLOCK_ID_PATTERN})\}}")
CODE_FENCE_RE = re.compile(r"^\s*(```|~~~)")

# Git log field/record separators (unit separator, record separator)
FIELD_SEPARATOR = "\x1f"
RECORD_SEPARATOR = "\x1e"
SHORT_HASH_LENGTH = 7
EMPTY_COMMITS_VALUE = "(none yet)"


def run_git(arguments: List[str], repository_root: Path) -> str:
    """
    Runs a git command inside the repository and returns its decoded standard output.

    Args:
        arguments: Git arguments without the leading `git`, e.g. ["log", "--all"]
        repository_root: Directory the command is executed in

    Returns:
        Standard output of the command decoded as UTF-8
    """
    result = subprocess.run(["git", *arguments], cwd=repository_root, capture_output=True, check=True)
    return result.stdout.decode("utf-8", errors="replace")


def find_repository_root() -> Path:
    """
    Resolves the top-level directory of the git repository containing the current working directory,
    so the script behaves identically regardless of the subdirectory it is launched from.

    Args:
        None

    Returns:
        Absolute path of the repository root
    """
    try:
        top_level = run_git(["rev-parse", "--show-toplevel"], Path.cwd()).strip()

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"ERROR: not inside a git repository, or git is unavailable. Reason: {e}", file=sys.stderr)
        sys.exit(2)

    return Path(top_level)


def split_trailer_ids(raw_value: str) -> List[str]:
    """
    Splits a trailer value (possibly several trailers joined by commas) into individual IDs.

    Args:
        raw_value: Raw trailer text such as "C1, I2" or "D-20260916-LP-1,D-20260917-LP-1"

    Returns:
        List of non-empty IDs in their original order
    """
    return [identifier for identifier in re.split(r"[,\s]+", raw_value.strip()) if identifier]


def collect_trailers_from_git(repository_root: Path) -> Tuple[Dict[str, List[Tuple[str, str]]], Dict[str, Set[str]]]:
    """
    Scans every commit reachable from any ref, oldest first, collecting `Decision:` and `Concept:`
    trailers. Multiple trailers of the same key on one commit are joined with commas by git, so each
    commit is a single record regardless of how many trailers it carries.

    Args:
        repository_root: Repository whose history is scanned

    Returns:
        Tuple of ({decision_id: [(short_hash, author_name), ...] in chronological order},
                  {block_id: {short_hash, ...}} for every block cited in a Concept trailer)
    """
    log_format = FIELD_SEPARATOR.join([
        "%H",
        "%an",
        "%(trailers:key=Decision,valueonly,separator=%x2C)",
        "%(trailers:key=Concept,valueonly,separator=%x2C)",
    ]) + RECORD_SEPARATOR
    output = run_git(["log", "--all", "--reverse", f"--format={log_format}"], repository_root)

    commits_by_decision: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    commits_by_block: Dict[str, Set[str]] = defaultdict(set)

    for record in output.split(RECORD_SEPARATOR):
        fields = record.strip("\n").split(FIELD_SEPARATOR)
        if len(fields) != 4:
            continue
        full_hash, author_name, decision_raw, concept_raw = fields
        short_hash = full_hash[:SHORT_HASH_LENGTH]

        # Records each decision once per commit, even if a trailer is repeated
        for decision_id in dict.fromkeys(split_trailer_ids(decision_raw)):
            commits_by_decision[decision_id].append((short_hash, author_name))

        for block_id in split_trailer_ids(concept_raw):
            commits_by_block[block_id].add(short_hash)

    return commits_by_decision, commits_by_block


def iterate_unfenced_lines(lines: List[str]):
    """
    Yields (index, line) for every line outside fenced code blocks, so that format examples such as the
    one in the DECISIONS.md header are never mistaken for real entries.

    Args:
        lines: Document lines without line terminators

    Returns:
        Generator of (line_index, line) tuples
    """
    inside_fence = False
    for index, line in enumerate(lines):
        if CODE_FENCE_RE.match(line):
            inside_fence = not inside_fence
            continue
        if not inside_fence:
            yield index, line


def parse_decisions_file(lines: List[str]) -> Tuple[Dict[str, Tuple[int, str]], Dict[str, List[str]]]:
    """
    Extracts, per decision entry, the location and value of its Commits field and the block IDs of its
    Linked to field.

    Args:
        lines: DECISIONS.md lines without line terminators

    Returns:
        Tuple of ({decision_id: (commits_line_index, commits_value)},
                  {decision_id: [linked_block_id, ...]})
    """
    commits_fields: Dict[str, Tuple[int, str]] = {}
    linked_blocks: Dict[str, List[str]] = {}
    current_decision_id = None

    for index, line in iterate_unfenced_lines(lines):
        if header_match := DECISION_HEADER_RE.match(line):
            current_decision_id = header_match.group(1)
            continue
        if current_decision_id is None:
            continue
        if commits_match := COMMITS_LINE_RE.match(line):
            commits_fields[current_decision_id] = (index, commits_match.group(1).strip())
        elif linked_match := LINKED_TO_LINE_RE.match(line):
            linked_blocks[current_decision_id] = split_trailer_ids(linked_match.group(1))

    return commits_fields, linked_blocks


def parse_report_anchors(report_path: Path) -> Set[str]:
    """
    Collects every `{#ID}` anchor defined in REPORT.md outside fenced code blocks.

    Args:
        report_path: Path to docs/REPORT.md

    Returns:
        Set of block IDs, e.g. {"C1", "I1", "E1"}
    """
    lines = report_path.read_text(encoding="utf-8").splitlines()
    return {anchor for _, line in iterate_unfenced_lines(lines) for anchor in REPORT_ANCHOR_RE.findall(line)}


def parse_cached_hashes(commits_value: str) -> List[str]:
    """
    Extracts the commit hashes listed in a Commits field value, ignoring the author annotations.

    Args:
        commits_value: Field value such as "a3f9c1e (L. Palou), b7e2201 (L. Palou)" or "(none yet)"

    Returns:
        Lowercase hashes in the order they appear
    """
    return [match.group(1).lower() for match in COMMIT_ENTRY_RE.finditer(commits_value)]


def format_commits_value(commit_list: List[Tuple[str, str]]) -> str:
    """
    Formats the canonical Commits field value for a decision.

    Args:
        commit_list: Chronological (short_hash, author_name) pairs taken from git trailers

    Returns:
        Comma-separated "hash (author)" entries, or the empty marker if no commit exists yet
    """
    if not commit_list:
        return EMPTY_COMMITS_VALUE
    return ", ".join(f"{short_hash} ({author_name})" for short_hash, author_name in commit_list)


def hash_matches_any(cached_hash: str, git_hashes: List[str]) -> bool:
    """
    Checks whether a cached hash (of any abbreviation length) refers to one of the git commits.

    Args:
        cached_hash: Hash as written in DECISIONS.md
        git_hashes: Short hashes collected from git trailers

    Returns:
        True if the cached hash and one of the git hashes are prefixes of each other
    """
    return any(cached_hash.startswith(git_hash) or git_hash.startswith(cached_hash) for git_hash in git_hashes)


def main() -> None:
    """
    Parses arguments, compares DECISIONS.md and REPORT.md against git history, prints every discrepancy,
    optionally rewrites stale Commits fields, and exits 0 (clean), 1 (drift remains) or 2 (setup error).

    Args:
        None

    Returns:
        None
    """
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="report drift only, exit 1 if found")
    mode.add_argument("--fix", action="store_true", help="rewrite Commits fields to match git history")
    args = parser.parse_args()

    repository_root = find_repository_root()
    decisions_path = repository_root / DECISIONS_RELATIVE_PATH
    report_path = repository_root / REPORT_RELATIVE_PATH

    if not decisions_path.exists():
        print(f"ERROR: {DECISIONS_RELATIVE_PATH} not found under {repository_root}.", file=sys.stderr)
        sys.exit(2)

    # Preserves the file's original line terminator when rewriting it
    raw_text = decisions_path.read_bytes().decode("utf-8")
    line_terminator = "\r\n" if "\r\n" in raw_text else "\n"
    lines = raw_text.splitlines()

    commits_by_decision, commits_by_block = collect_trailers_from_git(repository_root)
    commits_fields, linked_blocks = parse_decisions_file(lines)

    fixable_issues = 0
    unfixable_issues = 0

    # Stage 1: Commits cache versus Decision trailers
    for decision_id, (line_index, current_value) in commits_fields.items():
        git_commits = commits_by_decision.get(decision_id, [])
        git_hashes = [short_hash for short_hash, _ in git_commits]
        cached_hashes = parse_cached_hashes(current_value)

        invalid_hashes = [h for h in cached_hashes if not hash_matches_any(h, git_hashes)]
        missing_hashes = [h for h in git_hashes if not hash_matches_any(h, cached_hashes)]
        expected_value = format_commits_value(git_commits)

        if not invalid_hashes and not missing_hashes and current_value == expected_value:
            continue

        fixable_issues += 1
        print(f"DRIFT {decision_id}:")
        print(f"  DECISIONS.md: {current_value or '(empty)'}")
        print(f"  git history:  {expected_value}")
        if invalid_hashes:
            print(f"  not backed by a Decision trailer: {', '.join(invalid_hashes)}")
        if missing_hashes:
            print(f"  missing from the cache: {', '.join(missing_hashes)}")
        if args.fix:
            lines[line_index] = f"**Commits:** {expected_value}"

    # Stage 2: Decision trailers without a DECISIONS.md entry
    for decision_id in sorted(set(commits_by_decision) - set(commits_fields)):
        unfixable_issues += 1
        hashes = ", ".join(short_hash for short_hash, _ in commits_by_decision[decision_id])
        if DECISION_ID_RE.match(decision_id):
            print(f"UNDOCUMENTED {decision_id}: cited by commit(s) {hashes} but has no entry in {DECISIONS_RELATIVE_PATH}.")
        else:
            print(f"MALFORMED Decision trailer '{decision_id}' in commit(s) {hashes}: expected D-<YYYYMMDD>-<initials>-<n>.")

    # Stage 3: Block IDs cited in trailers or Linked to fields versus REPORT.md anchors
    if report_path.exists():
        report_anchors = parse_report_anchors(report_path)
        for block_id in sorted(set(commits_by_block) - report_anchors):
            unfixable_issues += 1
            print(f"UNKNOWN BLOCK {block_id}: cited in Concept trailer of commit(s) "
                  f"{', '.join(sorted(commits_by_block[block_id]))} but no {{#{block_id}}} anchor exists in {REPORT_RELATIVE_PATH}.")
        for decision_id, block_ids in linked_blocks.items():
            for block_id in block_ids:
                if block_id not in report_anchors:
                    unfixable_issues += 1
                    print(f"UNKNOWN BLOCK {block_id}: linked from {decision_id} but no {{#{block_id}}} anchor exists in {REPORT_RELATIVE_PATH}.")
    else:
        print(f"WARNING: {REPORT_RELATIVE_PATH} not found, block IDs were not validated.")

    if args.fix and fixable_issues:
        decisions_path.write_bytes((line_terminator.join(lines) + line_terminator).encode("utf-8"))
        print(f"Rewrote {fixable_issues} Commits field(s) in {DECISIONS_RELATIVE_PATH}.")
        fixable_issues = 0

    remaining_issues = fixable_issues + unfixable_issues
    if remaining_issues == 0:
        print("No drift found.")
        sys.exit(0)

    print(f"{remaining_issues} issue(s) remain.")
    sys.exit(1)


if __name__ == "__main__":
    main()
