# Research Lineage — Specification

Version 0.3.0. This document is the canonical definition of the framework; everything else (the skill, its templates, the install scripts, and the per-project scaffolds) is derived from it, not the other way around. Where any other file disagrees with this one, this one is correct and the other file is a bug.

## 1. Purpose

During a data science project three records of the same system tend to drift apart: the conceptual guide (what the system is), the decision trail (why it changed), and the repository history (what code resulted). The framework binds them through shared identifiers, so that the report is the entry point for understanding the project, the decision log is the entry point for understanding a change, and git (being immutable) is the ledger both of them refer back to. No database or external service is involved: every link is plain text inside the repository, and every query is a `git log` or a text search.

## 2. Framework repository layout

The framework lives in its own GitHub repository, which is the single source of truth for the skill that Claude Code loads:

```
research-lineage/
├── SPEC.md                             # this file
├── README.md                           # quick start, links to SPEC.md
├── CHANGELOG.md                        # framework's own version history
├── .gitignore
├── .gitattributes                      # LF endings for scripts, hooks, templates
├── skill/
│   └── research-lineage/      # the directory linked into ~/.claude/skills/
│       ├── SKILL.md                    # trigger, scaffolding and ongoing rules, `version:`
│       └── templates/
│           ├── REPORT.skeleton.md      # anchored report template
│           ├── DECISIONS.skeleton.md   # empty log, header and entry format only
│           ├── CLAUDE.fragment.md      # rules added to a project's CLAUDE.md
│           ├── reconcile.py            # drift checker, --check / --fix
│           └── pre-push.hook           # optional hook running reconcile.py --check
├── scripts/
│   ├── install.sh                      # symlinks skill/ into ~/.claude/skills/ (macOS, Linux, Git Bash)
│   └── install.ps1                     # same via a directory junction (Windows)
├── tests/
│   └── test_reconcile.py               # end-to-end tests of reconcile.py (pytest)
└── examples/
    └── worked-example/                 # filled REPORT.md + DECISIONS.md, reference only
```

`reconcile.py` depends only on the Python 3.8+ standard library and git 2.29+ (for the `separator` option of `%(trailers)`); pytest is needed only to develop the framework itself.

## 3. Deployment model

The skill is never a separately maintained copy. `scripts/install.sh` symlinks it into the personal skills directory:

```bash
ln -s "$(pwd)/skill/research-lineage" ~/.claude/skills/research-lineage
```

Since it is a link rather than a copy, editing the repository edits what Claude Code loads, with no sync step and no drift between "the standard" and "what is installed", and a `git pull` updates the skill on every machine it is linked from. Two safety rules apply to both install scripts: an existing link at the destination is replaced, whereas an existing real directory is never deleted (it may be a hand-edited copy) and the script aborts instead; and the scripts never fall back to copying, which Git Bash on Windows does silently for `ln -s` unless native symlinks are forced (`MSYS=winsymlinks:nativestrict`). On Windows without Developer Mode, `scripts/install.ps1` creates a directory junction, which behaves like a symlink for this purpose and needs no administrator rights.

## 4. Artifact schemas

### 4.1 `docs/REPORT.md` (per project)

The report follows the structure and writing rules of the `reporting` skill (Theoretical Scope, Goal, Proposed Solution, Concepts, Implementation, Experiments; dense blocks, no redundancy, definition/role/interaction order in Concepts). The framework adds exactly one thing: every Concept, Implementation, and Experiment heading carries an anchor, as in `### LSTM {#C1}`. IDs are sequential per section, are never renumbered or reused once committed (a removed block leaves a gap), and a new block takes the next free number in its section.

### 4.2 `docs/DECISIONS.md` (per project)

An append-only log with one entry per design decision, where a design decision is a change justified by data, a benchmark, or a project requirement (a plain bug fix is not one):

```markdown
### D-20260916-LP-1 — Switch loss to focal loss
**Author:** Lluc Palou
**Date:** 2026-09-16
**Linked to:** C2, I2, E1
**Supersedes:** D-20260910-LP-1          (optional, omitted when empty)
**Context:** [Empirical or requirement-driven justification.]
**Decision:** [What was decided.]
**Status:** Accepted, pending implementation | Implemented | Superseded by D-...
**Commits:** (none yet) | <short hash> (<author>), ...
```

Each field sits on a single line starting with its bold label, except `Context` and `Decision`, whose text may wrap. The entry is partitioned into two kinds of fields, which is what "append-only" means precisely:

| Kind | Fields | Rule |
|---|---|---|
| Content | Author, Date, Linked to, Supersedes, Context, Decision | Written once, never edited. A correction is a new entry with `Supersedes:`. |
| State | Status, Commits | Updated as the decision progresses; `Status` of a superseded entry becomes `Superseded by D-...`. |

`Commits` is a cache, never authoritative on its own: it is maintained by `reconcile.py --fix` (section 4.5) and must always be a subset of what the commit trailers show. Entries are never removed or reordered, and new ones are appended at the end. Anything inside a fenced code block (such as the format example in the file's header) is ignored by tooling.

### 4.3 Commit trailers

```
feat(I1): sliding-window feature extraction for OHLCV

Concept: I1, C1
Decision: D-20260916-LP-1
```

Trailers are placed in the last paragraph of the message, one per line, with no blank line between them (git's trailer syntax). `Concept:` lists the report blocks a commit implements or modifies; `Decision:` names the decision a commit executes and appears only on such commits. A commit may carry several trailers of either key, which git joins when reading them back with `git log --format='%(trailers:key=Decision,valueonly,separator=%x2C)'`. The trailers are the canonical record of which commit implemented what.

### 4.4 `CLAUDE.md` fragment

`templates/CLAUDE.fragment.md` begins with a `## Research Lineage` heading and records the framework version the project was scaffolded against (substituted from `SKILL.md`'s `version:` into a `{{FRAMEWORK_VERSION}}` placeholder). It instructs Claude Code to read `docs/REPORT.md` and `docs/DECISIONS.md` before implementation work, to reference block IDs instead of restating content, to log a decision before writing the code for it, to tag commits with both trailers, to refresh the `Commits` cache in a separate commit (section 6), and to respect the field mutability rules of section 4.2.

### 4.5 `scripts/reconcile.py`

The script resolves the repository root through git (so it runs from any subdirectory), reads and writes files as UTF-8 while preserving their line endings, and scans every commit reachable from any ref (`git log --all`) in chronological order. It reports the following issues:

| Issue | Meaning | Fixed by `--fix` |
|---|---|---|
| `DRIFT` (missing) | A commit carries `Decision: D-x` but is absent from D-x's `Commits` field | Yes |
| `DRIFT` (not backed) | A hash in D-x's `Commits` field has no matching `Decision: D-x` trailer (subset rule violated) | Yes |
| `DRIFT` (format) | Same commits, but not in the canonical chronological `hash (author)` form | Yes |
| `UNDOCUMENTED` | A well-formed decision ID appears in a trailer but has no entry in `DECISIONS.md` | No |
| `MALFORMED` | A `Decision:` trailer value does not follow the ID grammar | No |
| `UNKNOWN BLOCK` | A block ID in a `Concept:` trailer or a `Linked to:` field has no `{#ID}` anchor in `REPORT.md` | No |

Hashes are written as 7-character abbreviations but matched by prefix, so a longer abbreviation written by hand is accepted. `--check` changes nothing; `--fix` rewrites only the stale `Commits` lines and then reports whatever remains. Both are idempotent. The exit code is 0 when no issue remains, 1 when any does (which makes `--check` usable as a `pre-push` hook), and 2 on a setup error (not a git repository, or no `DECISIONS.md`); a missing `REPORT.md` only skips the block validation, with a warning.

### 4.6 `pre-push` hook (optional)

`templates/pre-push.hook` runs `reconcile.py --check` from the repository root with the first available Python interpreter, blocking the push while drift remains; `git push --no-verify` bypasses it once. It is installed to `.git/hooks/pre-push` only with the user's consent and never over an existing hook.

## 5. ID grammar

| Form | Meaning | Collision risk |
|---|---|---|
| `C<n>`, `I<n>`, `E<n>` | Concept / Implementation / Experiment block in `REPORT.md` | None: single document, sequential, never reused |
| `D-<YYYYMMDD>-<initials>-<n>` | Decision, dated, attributed, the nth by that author that day (starting at 1) | None, even across concurrent branches, as long as initials are unique among contributors |
| `Concept:` trailer | Report block(s) a commit implements | n/a |
| `Decision:` trailer | Decision(s) a commit executes | n/a |

Initials are letters only (`[A-Za-z]+`) and are derived from `git config user.name`; two contributors with the same initials must agree on distinct ones (e.g. `LP` and `LPa`).

## 6. Interaction model

```
E1 (experiment surfaces a finding)
  -> D-... appended to DECISIONS.md (justified by E1, linked to C/I blocks)
      -> implementing commits (trailers: Decision, Concept)
          -> REPORT.md block patched, only if the decision changed a claim
             (same or following commit, carrying the Decision trailer)
              -> reconcile.py --fix, committed separately with no Decision trailer,
                 Status set to Implemented once the decision is complete
```

The cache refresh is a separate commit because a commit cannot contain its own hash: amending to record it would change the hash again. That refresh commit must not carry a `Decision:` trailer, since it would otherwise cite itself and leave the cache permanently stale. Given this chain, `git log --all --grep=<ID>` on any block or decision ID returns the complete causal trail, with no separate database.

## 7. Per-project scaffold

Invoking the skill in a target repository (a git repository; the skill offers `git init` otherwise) creates, only where absent and never overwriting:

- `docs/REPORT.md` from `REPORT.skeleton.md`, if no report exists yet; an existing report without anchors is anchored only after asking.
- `docs/DECISIONS.md` from `DECISIONS.skeleton.md`.
- `CLAUDE.md`, created from the fragment, or with the fragment appended if the file exists; left untouched if it already contains the `## Research Lineage` heading or the legacy `## Report-Decision Framework` heading (versions before 0.3.0).
- `scripts/reconcile.py`, copied.
- `.git/hooks/pre-push`, optionally and only with consent.

The resulting project layout is therefore:

```
<project>/
├── CLAUDE.md                 # includes the framework section and its version
├── docs/
│   ├── REPORT.md
│   └── DECISIONS.md
├── scripts/
│   └── reconcile.py
└── ...                       # the project's own code
```

The scaffold ends with `reconcile.py --check` (expected to report no drift) and is committed as `chore: scaffold research-lineage framework v<version>`.

## 8. Framework versioning

Once the framework is used across several projects, it must be able to change without silently reinterpreting old projects under a new schema. `SKILL.md` carries a semantic version (`version:` in its frontmatter), `CHANGELOG.md` records what changed, git tags (`v<version>`) mark releases, and every project's `CLAUDE.md` records the version it was scaffolded against. A schema change bumps the minor version (major from 1.0.0 onwards), and the version string in this file, `SKILL.md`, and `CHANGELOG.md` must match. Moving a project to a newer version is a deliberate, per-project migration proposed by the skill and accepted by the user, which updates the recorded version in the same commit; existing `DECISIONS.md` entries are never rewritten to fit a new schema.

## 9. Building the repository

The repository is built, or rebuilt from scratch, in the following order, each step depending only on the previous ones:

1. Create the GitHub repository `research-lineage` (no template, no licence file needed for private use) and clone it.
2. Add `.gitignore` (`__pycache__/`, `*.pyc`, `.pytest_cache/`) and `.gitattributes` (LF for `*.sh`, `*.hook`, `*.py`, `*.md`; CRLF for `*.ps1`), before any script is committed, so Windows checkouts never produce CRLF shell scripts.
3. Write this `SPEC.md`, then derive from it `skill/research-lineage/SKILL.md` (frontmatter `name`, `description`, `version`) and the five files under `templates/` described in section 4.
4. Write `scripts/install.sh` and `scripts/install.ps1` following section 3, and mark the shell files executable (`git update-index --chmod=+x scripts/install.sh skill/research-lineage/templates/reconcile.py skill/research-lineage/templates/pre-push.hook`).
5. Write `tests/test_reconcile.py`, covering at least every row of the table in section 4.5, idempotency of `--fix`, empty `Commits` fields, multiple trailers per commit, CRLF preservation, and execution from a subdirectory; run `python -m pytest tests`.
6. Fill `examples/worked-example/` with a small, consistent `REPORT.md` / `DECISIONS.md` pair in which every ID cited in `DECISIONS.md` exists as an anchor in `REPORT.md`.
7. Write `README.md` (quick start, link to this file) and the `CHANGELOG.md` entry, check that the version string matches in `SPEC.md`, `SKILL.md`, and `CHANGELOG.md`, then commit, tag `v<version>`, and push with `--tags`.
8. On each machine, clone and run the install script, then invoke the skill in a sample repository and confirm that `reconcile.py --check` reports no drift.

## 10. Status

v0.2.0: specification, skill, templates, install scripts, and tests complete (see `CHANGELOG.md`). Not yet applied to a real project. Open items: extending the `reporting` skill itself to emit `{#ID}` anchors by default (currently the framework skill instructs Claude to add them), and CI running `tests/` on push.
