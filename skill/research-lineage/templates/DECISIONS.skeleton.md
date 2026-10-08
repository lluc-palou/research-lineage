# Decisions

Append-only log of design decisions made during development, each linked to
the report blocks it affects and to the commits that implemented it. Entries
are never removed or reordered, and their content fields (Author, Date,
Linked to, Supersedes, Context, Decision) are never edited. Only the two
state fields change after an entry is written: `Status` (as the decision
progresses or is superseded) and `Commits` (a cache maintained by
`scripts/reconcile.py --fix`). A correction is a new entry that supersedes
an old one.

Entry format:

```markdown
### D-<YYYYMMDD>-<author-initials>-<n> — <short title>
**Author:** <name>
**Date:** <YYYY-MM-DD>
**Linked to:** <report block IDs, e.g. C1, I1, E1>
**Supersedes:** <D-... this entry replaces; omit the line if none>
**Context:** <the empirical result, benchmark, or project requirement that
motivated this decision>
**Decision:** <what was decided>
**Status:** Accepted, pending implementation | Implemented | Superseded by D-...
**Commits:** (none yet)
```

---

<!-- New entries below, most recent last. -->
