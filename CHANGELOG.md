# Changelog

All notable changes to the framework itself (not to any project using it) are recorded here. Projects record the version they were scaffolded against in their `CLAUDE.md`; moving a project to a newer version is a deliberate migration (SPEC.md section 8).

## 0.3.0 - 2026-10-08
- Renamed from `report-decision-framework` to `research-lineage` (repository, skill directory and `name`, install targets, documentation). The new name reflects the full lineage traced, from report concepts through decisions, justifications and impact to implementation and git history.
- `CLAUDE.fragment.md` heading is now `## Research Lineage`; the skill still recognizes the legacy `## Report-Decision Framework` heading, so projects scaffolded against earlier versions are not appended to twice.
- Re-run the install script after updating: the skill is now linked as `~/.claude/skills/research-lineage`, and the old `report-decision-framework` link should be removed.

## 0.2.0 - 2026-09-29
Schema:
- `DECISIONS.md`: optional `**Supersedes:**` field; content fields are immutable, only `Status` and `Commits` are mutable; empty cache is written `(none yet)`.
- Cache refresh rule: `Commits` fields are updated by `reconcile.py --fix` in a separate commit without a `Decision:` trailer, never by amending.

`reconcile.py`:
- Fixed: a commit with several `Decision:` trailers only recorded the first one.
- Fixed: an empty `**Commits:**` field was not recognized, so the entry was reported as undocumented.
- Fixed: `--fix` wrote commits newest-first; they are now chronological.
- Fixed: only worked from the repository root; now resolves it via git.
- Fixed: files read and written with the platform encoding and line endings; now UTF-8 with the original terminators preserved.
- Fixed: the format example inside the skeleton's code fence was parsed as an entry.
- New: enforces the subset rule (cached hashes not backed by a trailer are errors), accepts any hash abbreviation length.
- New: validates block IDs in `Concept:` trailers and `Linked to:` fields against `{#ID}` anchors in `REPORT.md`, and flags malformed decision IDs.
- New: exit code 2 for setup errors (no repo, no `DECISIONS.md`).

Tooling:
- `templates/pre-push.hook`, optional hook running `reconcile.py --check`.
- `scripts/install.ps1` (junction-based, no admin rights) for Windows; `install.sh` no longer deletes a real directory and refuses to fall back to a copy.
- `.gitattributes` pins LF endings for scripts and hooks.
- `tests/test_reconcile.py` (pytest, end-to-end against throwaway repos).
- `CLAUDE.fragment.md` takes the version from `SKILL.md` through a `{{FRAMEWORK_VERSION}}` placeholder instead of a hard-coded value.

## 0.1.0 - 2026-09-29
- Initial specification (`SPEC.md`).
- Skill scaffold: `SKILL.md`, `REPORT.skeleton.md`, `DECISIONS.skeleton.md`, `CLAUDE.fragment.md`, `reconcile.py`.
- Install script (symlink-based deployment).
- Worked example under `examples/worked-example/`.
