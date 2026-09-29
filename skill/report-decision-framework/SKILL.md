---
name: report-decision-framework
description: Scaffold and maintain the report-decision traceability framework, linking a project's conceptual REPORT.md, its DECISIONS.md design-decision log, and its git commits. Trigger when starting a new data science, ML, or research project, when asked to set up decision tracking or traceability, or when asked to link a project's report to its repository history.
version: 0.1.0
---

# Report-Decision Framework Skill

Full specification: see `SPEC.md` in this skill's parent repository (https://github.com/<user>/report-decision-framework, or wherever this repo is hosted).

## When to apply

Trigger on requests like: "set up the decision framework here", "scaffold traceability for this project", "link this report to the repo", or when a new project's `docs/REPORT.md` already exists and needs a decision log wired to it.

## Scaffolding (first invocation in a project)

Create, only where absent:

1. `docs/REPORT.md` from `templates/REPORT.skeleton.md`, if no report exists yet. If one exists without `{#ID}` anchors, ask before adding them (anchoring an existing report changes its structure).
2. `docs/DECISIONS.md` from `templates/DECISIONS.skeleton.md`.
3. `CLAUDE.md`: create it with the content of `templates/CLAUDE.fragment.md` if absent, or append that content under a `## Report-Decision Framework` heading if `CLAUDE.md` already exists.
4. `scripts/reconcile.py`, copied from `templates/reconcile.py`.

Record the framework version (from this file's frontmatter) in the appended `CLAUDE.md` section, so a later framework change is a deliberate migration, not a silent reinterpretation.

## Ongoing behavior (every session in a scaffolded project)

- Read `docs/REPORT.md` and `docs/DECISIONS.md` before implementation work. Reference block IDs (`{#C1}`, `{#I1}`, `{#E1}`), do not restate their content.
- Before implementing a change that is a design decision (justified by data, a benchmark, or a project requirement rather than a bug fix), append an entry to `docs/DECISIONS.md` first, following `DECISIONS.skeleton.md`'s format. Generate the ID as `D-<YYYYMMDD>-<author-initials>-<n>`.
- Tag every commit implementing report-linked work with trailers:
  ```
  Concept: <ID, ...>
  Decision: <ID>
  ```
  (`Decision:` only if the commit executes a logged decision.)
- After committing, append the commit's short hash and author to the relevant decision's `Commits` field in `docs/DECISIONS.md`.
- If a decision changes a claim already made in `docs/REPORT.md` (not just an implementation detail), patch that block in the same or a following commit, and reference the decision ID in the commit message.
- Do not rewrite `docs/DECISIONS.md` history. It is append-only; corrections are new entries with `Status: Supersedes D-...` / `Superseded by D-...`.

## Reconciliation

`docs/DECISIONS.md`'s `Commits` fields are a cache, not authoritative. Run `python scripts/reconcile.py --check` periodically or before considering a decision closed, to catch commits made outside this workflow. Use `--fix` to rewrite the fields from git history.
