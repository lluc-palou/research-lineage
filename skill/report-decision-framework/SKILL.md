---
name: report-decision-framework
description: Scaffold and maintain the report-decision traceability framework, linking a project's conceptual REPORT.md, its DECISIONS.md design-decision log, and its git commits. Trigger when starting a new data science, ML, or research project, when asked to set up decision tracking or traceability, when asked to link a project's report to its repository history, or when working in a repo whose CLAUDE.md contains a "Report-Decision Framework" section.
version: 0.2.0
---

# Report-Decision Framework Skill

Full specification: `SPEC.md` at the root of the framework repository. This skill directory is symlinked from that repository, so the file is at `../../SPEC.md` relative to this file's resolved location. SPEC.md is authoritative; if this file and SPEC.md disagree, follow SPEC.md and point out the discrepancy.

## When to apply

Trigger on requests like: "set up the decision framework here", "scaffold traceability for this project", "link this report to the repo", or when a new project's `docs/REPORT.md` already exists and needs a decision log wired to it.

## Scaffolding (first invocation in a project)

The target must be a git repository (offer `git init` if it is not). Create, only where absent, never overwriting:

1. `docs/REPORT.md` from `templates/REPORT.skeleton.md`, if no report exists yet. When filling it, follow the `reporting` skill's writing rules if that skill is available, and add a `{#ID}` anchor to every Concept (`C<n>`), Implementation (`I<n>`) and Experiment (`E<n>`) heading, numbered sequentially per section. If a report exists without anchors, ask before adding them (anchoring an existing report changes its structure).
2. `docs/DECISIONS.md` from `templates/DECISIONS.skeleton.md`.
3. `CLAUDE.md`: take `templates/CLAUDE.fragment.md`, replace `{{FRAMEWORK_VERSION}}` with the `version` in this file's frontmatter, then create `CLAUDE.md` with it if absent, or append it verbatim (it already carries its `## Report-Decision Framework` heading) if `CLAUDE.md` exists. If that heading is already present, leave `CLAUDE.md` untouched and report the recorded version instead.
4. `scripts/reconcile.py`, copied from `templates/reconcile.py`.
5. Optionally, with the user's consent, `.git/hooks/pre-push` from `templates/pre-push.hook` (made executable). Never replace an existing hook; show the one-line call to add to it instead.

Finish with `python scripts/reconcile.py --check` (expected: "No drift found.") and suggest committing the scaffold as `chore: scaffold report-decision framework v<version>`.

## Ongoing behavior (every session in a scaffolded project)

- Read `docs/REPORT.md` and `docs/DECISIONS.md` before implementation work. Reference block IDs (`C1`, `I1`, `E1`), do not restate their content.
- Before implementing a change that is a design decision (justified by data, a benchmark, or a project requirement rather than a bug fix), append an entry to `docs/DECISIONS.md` first, following the skeleton's format. Generate the ID as `D-<YYYYMMDD>-<author-initials>-<n>`, with `<n>` one more than the highest existing `<n>` for that author and date (1 if none). Take the author from `git config user.name`.
- Tag every commit implementing report-linked work with trailers in the final paragraph of the message:
  ```
  Concept: <ID, ...>
  Decision: <ID>
  ```
  (`Decision:` only if the commit executes a logged decision.)
- Never amend a commit to record its own hash. After implementing commits land, run `python scripts/reconcile.py --fix` and commit the refreshed `Commits` fields separately, without a `Decision:` trailer, updating the entry's `Status` to `Implemented` in the same commit when the decision is complete.
- If a decision changes a claim already made in `docs/REPORT.md` (not just an implementation detail), patch that block in the same or a following commit carrying the decision's `Decision:` trailer. New blocks get the next free ID in their section; existing IDs are never renumbered or reused.
- `docs/DECISIONS.md` is append-only: only `Status` and `Commits` may change in an existing entry. Corrections are new entries with `**Supersedes:** D-...`, and the old entry's `Status` becomes `Superseded by D-...`.

## Reconciliation

`docs/DECISIONS.md`'s `Commits` fields are a cache, git trailers are authoritative. `python scripts/reconcile.py --check` reports stale or invalid caches, trailers citing undocumented decisions, and block IDs (in `Concept:` trailers or `Linked to:` fields) with no anchor in `docs/REPORT.md`; it exits 1 on any of them. `--fix` rewrites the stale `Commits` fields from git history; the other issues need a human (or Claude) to add the missing entry or anchor.

## Framework upgrades

If a project's `CLAUDE.md` records an older framework version than this file, do not silently apply the new rules to existing entries. Point out the difference, summarize the relevant `CHANGELOG.md` entries, and migrate only if the user agrees, updating the recorded version in the same commit.
