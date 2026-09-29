"""
Reconciliation Script Tests

End-to-end tests for skill/report-decision-framework/templates/reconcile.py. Each test builds a throwaway
git repository with a docs/REPORT.md, a docs/DECISIONS.md and commits carrying `Decision:` / `Concept:`
trailers, runs the script as a subprocess from that repository, and asserts on its exit code, output and
rewritten DECISIONS.md.
"""

import sys
import shutil
import subprocess
from pathlib import Path
from typing import List

import pytest

RECONCILE_SCRIPT = Path(__file__).resolve().parents[1] / "skill" / "report-decision-framework" / "templates" / "reconcile.py"

REPORT_TEXT = """# Project

## Concepts

### LSTM {#C1}
Text.

## Implementation

### Training Loop {#I1}
Text.
"""

DECISION_TEMPLATE = """# Decisions

```markdown
### D-<YYYYMMDD>-<author-initials>-<n> — <short title>
**Commits:** (none yet)
```

---

### D-20260916-LP-1 — Switch loss to focal loss
**Author:** Lluc Palou
**Date:** 2026-09-16
**Linked to:** {linked_to}
**Context:** E1 showed NEUTRAL collapse.
**Decision:** Use focal loss.
**Status:** Accepted, pending implementation
**Commits:**{commits}
"""


def run_git(repository: Path, arguments: List[str]) -> str:
    """
    Runs a git command in the test repository with a fixed identity.

    Args:
        repository: Test repository root
        arguments: Git arguments without the leading `git`

    Returns:
        Standard output of the command, stripped
    """
    identity = ["-c", "user.name=Lluc Palou", "-c", "user.email=lluc@example.com", "-c", "core.autocrlf=false"]
    result = subprocess.run(["git", *identity, *arguments], cwd=repository, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def commit(repository: Path, message: str) -> str:
    """
    Creates an empty commit with the given message.

    Args:
        repository: Test repository root
        message: Full commit message, including trailers

    Returns:
        Seven-character short hash of the new commit
    """
    run_git(repository, ["commit", "--allow-empty", "-q", "-m", message])
    return run_git(repository, ["rev-parse", "HEAD"])[:7]


def run_reconcile(repository: Path, mode: str, working_directory: Path = None) -> subprocess.CompletedProcess:
    """
    Runs reconcile.py in the given mode.

    Args:
        repository: Test repository root
        mode: "--check" or "--fix"
        working_directory: Directory to launch from, defaults to the repository root

    Returns:
        Completed process with decoded stdout/stderr
    """
    return subprocess.run([sys.executable, str(RECONCILE_SCRIPT), mode], cwd=working_directory or repository,
                          capture_output=True, text=True, encoding="utf-8")


def write_decisions(repository: Path, commits: str = " (none yet)", linked_to: str = "C1, I1",
                    line_terminator: str = "\n") -> Path:
    """
    Writes docs/DECISIONS.md with a single decision entry.

    Args:
        repository: Test repository root
        commits: Raw text placed right after `**Commits:**`
        linked_to: Value of the Linked to field
        line_terminator: "\n" or "\r\n"

    Returns:
        Path to the written file
    """
    decisions_path = repository / "docs" / "DECISIONS.md"
    text = DECISION_TEMPLATE.format(commits=commits, linked_to=linked_to).replace("\n", line_terminator)
    decisions_path.write_bytes(text.encode("utf-8"))
    return decisions_path


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """
    Creates an initialized git repository containing docs/REPORT.md and a DECISIONS.md with one decision.

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        Repository root
    """
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    run_git(tmp_path, ["init", "-q"])
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "REPORT.md").write_text(REPORT_TEXT, encoding="utf-8")
    write_decisions(tmp_path)
    return tmp_path


def test_clean_repository_passes(repository: Path) -> None:
    result = run_reconcile(repository, "--check")
    assert result.returncode == 0, result.stdout
    assert "No drift found." in result.stdout


def test_missing_commit_is_reported_then_fixed_idempotently(repository: Path) -> None:
    first_hash = commit(repository, "feat(I1): focal loss\n\nConcept: I1, C1\nDecision: D-20260916-LP-1")
    second_hash = commit(repository, "fix(I1): gamma\n\nDecision: D-20260916-LP-1")

    check = run_reconcile(repository, "--check")
    assert check.returncode == 1
    assert "DRIFT D-20260916-LP-1" in check.stdout

    fix = run_reconcile(repository, "--fix")
    assert fix.returncode == 0, fix.stdout
    text = (repository / "docs" / "DECISIONS.md").read_text(encoding="utf-8")
    assert f"**Commits:** {first_hash} (Lluc Palou), {second_hash} (Lluc Palou)" in text

    # A second fix is a no-op and the fenced format example stays untouched
    assert run_reconcile(repository, "--fix").stdout.strip() == "No drift found."
    assert (repository / "docs" / "DECISIONS.md").read_text(encoding="utf-8") == text
    assert "### D-<YYYYMMDD>-<author-initials>-<n> — <short title>\n**Commits:** (none yet)" in text


def test_empty_commits_field_is_recognized(repository: Path) -> None:
    write_decisions(repository, commits="")
    commit_hash = commit(repository, "feat: x\n\nDecision: D-20260916-LP-1")
    assert run_reconcile(repository, "--fix").returncode == 0
    assert f"**Commits:** {commit_hash} (Lluc Palou)" in (repository / "docs" / "DECISIONS.md").read_text(encoding="utf-8")


def test_multiple_decision_trailers_on_one_commit(repository: Path) -> None:
    commit_hash = commit(repository, "feat: x\n\nDecision: D-20260916-LP-1\nDecision: D-20260917-LP-1")
    result = run_reconcile(repository, "--fix")
    assert result.returncode == 1
    assert f"UNDOCUMENTED D-20260917-LP-1: cited by commit(s) {commit_hash}" in result.stdout
    assert f"**Commits:** {commit_hash} (Lluc Palou)" in (repository / "docs" / "DECISIONS.md").read_text(encoding="utf-8")


def test_cached_hash_without_trailer_violates_subset_rule(repository: Path) -> None:
    write_decisions(repository, commits=" deadbee (Lluc Palou)")
    result = run_reconcile(repository, "--check")
    assert result.returncode == 1
    assert "not backed by a Decision trailer: deadbee" in result.stdout


def test_longer_cached_hash_matches_short_hash(repository: Path) -> None:
    commit(repository, "feat: x\n\nDecision: D-20260916-LP-1")
    full_hash = run_git(repository, ["rev-parse", "HEAD"])
    write_decisions(repository, commits=f" {full_hash[:12]} (Lluc Palou)")
    result = run_reconcile(repository, "--check")
    assert "not backed" not in result.stdout and "missing from the cache" not in result.stdout


def test_unknown_block_ids_are_reported(repository: Path) -> None:
    write_decisions(repository, linked_to="C1, E9")
    commit(repository, "feat: x\n\nConcept: C7")
    result = run_reconcile(repository, "--check")
    assert result.returncode == 1
    assert "UNKNOWN BLOCK C7" in result.stdout
    assert "UNKNOWN BLOCK E9: linked from D-20260916-LP-1" in result.stdout


def test_malformed_decision_trailer_is_reported(repository: Path) -> None:
    commit(repository, "feat: x\n\nDecision: focal-loss")
    result = run_reconcile(repository, "--check")
    assert result.returncode == 1
    assert "MALFORMED Decision trailer 'focal-loss'" in result.stdout


def test_crlf_line_endings_are_preserved(repository: Path) -> None:
    decisions_path = write_decisions(repository, line_terminator="\r\n")
    commit(repository, "feat: x\n\nDecision: D-20260916-LP-1")
    assert run_reconcile(repository, "--fix").returncode == 0
    raw_bytes = decisions_path.read_bytes()
    assert raw_bytes.count(b"\r\n") == raw_bytes.count(b"\n")


def test_runs_from_a_subdirectory(repository: Path) -> None:
    subdirectory = repository / "src" / "models"
    subdirectory.mkdir(parents=True)
    result = run_reconcile(repository, "--check", working_directory=subdirectory)
    assert result.returncode == 0, result.stdout + result.stderr


def test_missing_decisions_file_is_a_setup_error(repository: Path) -> None:
    (repository / "docs" / "DECISIONS.md").unlink()
    result = run_reconcile(repository, "--check")
    assert result.returncode == 2
