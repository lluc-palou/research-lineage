## Report-Decision Framework

Scaffolded against framework version: 0.1.0 (see report-decision-framework repo for the spec).

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
ID format: `D-<YYYYMMDD>-<author-initials>-<n>`. Tag the implementing
commit(s) with:
```
Decision: <ID>
```
and append the commit's short hash and author to that decision's `Commits`
field after committing.

If a decision changes a claim already made in `docs/REPORT.md`, patch that
block in the same or a following commit, referencing the decision ID in the
commit message.

`docs/DECISIONS.md` is append-only. Never edit or delete a past entry;
corrections are new entries with `Status: Supersedes D-...` /
`Superseded by D-...`.

Periodically run `python scripts/reconcile.py --check` to catch drift
between `docs/DECISIONS.md` and actual git history (e.g. commits made
outside this workflow).
