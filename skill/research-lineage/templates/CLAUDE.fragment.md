## Research Lineage

Scaffolded against framework version: {{FRAMEWORK_VERSION}} (see the
research-lineage repo's SPEC.md for the full specification).

Read `docs/REPORT.md` before any implementation work. It is the conceptual
source of truth. Reference its block IDs (`{#C1}`, `{#I1}`, `{#E1}`), do not
restate their content.

Read `docs/DECISIONS.md` for accepted design decisions before proposing
changes to anything already decided.

When implementing or modifying a component tied to a report block, tag the
commit with a trailer:
```
Concept: <ID, ...>
```

When a design decision is made (a change justified by data, a benchmark, or
a project requirement rather than a plain bug fix), append an entry to
`docs/DECISIONS.md` before writing the code, using the format in that file.
ID format: `D-<YYYYMMDD>-<author-initials>-<n>`, where `<n>` is one more than
the highest `<n>` that author already has for that date. Tag the
implementing commit(s) with:
```
Decision: <ID>
```
Trailers go in the last paragraph of the commit message, one per line,
with no blank line between them.

Never amend a commit to record its own hash. Refresh the `Commits` cache
with `python scripts/reconcile.py --fix` and commit the result separately
(e.g. `docs(decisions): refresh commit cache`) without a `Decision:`
trailer. Set the entry's `Status` to `Implemented` in that same commit once
the decision is fully implemented.

If a decision changes a claim already made in `docs/REPORT.md`, patch that
block in the same or a following commit, referencing the decision ID in the
commit message (`Decision:` trailer).

`docs/DECISIONS.md` is append-only. Never delete or reorder entries, and
never edit their content fields; only `Status` and `Commits` may change.
Corrections are new entries with a `**Supersedes:** D-...` field, and the
superseded entry's `Status` becomes `Superseded by D-...`.

Run `python scripts/reconcile.py --check` before considering a decision
closed and before pushing (a `pre-push` hook may already do it).
