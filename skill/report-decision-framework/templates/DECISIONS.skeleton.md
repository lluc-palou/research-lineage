# Decisions

Append-only log of design decisions made during development, each linked to
the report blocks it affects and to the commits that implemented it. Do not
edit or remove past entries. A correction is a new entry that supersedes an
old one.

Entry format:

```markdown
### D-<YYYYMMDD>-<author-initials>-<n> — <short title>
**Author:** <name>
**Date:** <YYYY-MM-DD>
**Linked to:** <report block IDs, e.g. C1, I1, E1>
**Context:** <the empirical result, benchmark, or project requirement that
motivated this decision>
**Decision:** <what was decided>
**Status:** Accepted, pending implementation | Implemented | Superseded by D-...
**Commits:** <short hash (author), ...>  (populated as work lands, see
scripts/reconcile.py)
```

---

<!-- New entries below, most recent last. -->
