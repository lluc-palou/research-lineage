# Report-Decision Framework

Links a project's conceptual report, its design-decision log, and its git history, so a concept, a decision, and the code that implements it stay traceable to each other without a separate database.

Full definition: [SPEC.md](SPEC.md).

## Quick start

```bash
git clone <this-repo-url>
cd report-decision-framework
./scripts/install.sh
```

This symlinks `skill/report-decision-framework/` into `~/.claude/skills/`, so it's available in every project Claude Code works on. Editing this repo edits the skill immediately, no rebuild step.

In any project, invoke it (e.g. "set up the decision framework here") to scaffold `docs/REPORT.md`, `docs/DECISIONS.md`, the `CLAUDE.md` rules, and `scripts/reconcile.py`.

See `examples/worked-example/` for a filled pair of `REPORT.md` / `DECISIONS.md`.
