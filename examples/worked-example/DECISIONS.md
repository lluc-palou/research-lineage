# Decisions

Append-only log of design decisions made during development, each linked to
the report blocks it affects and to the commits that implemented it. Do not
edit or remove past entries. A correction is a new entry that supersedes an
old one.

---

### D-20260916-LP-1 — Switch loss to focal loss
**Author:** L. Palou
**Date:** 2026-09-16
**Linked to:** C1, C2, I2, E1
**Context:** Cross-entropy training left the classifier predicting NEUTRAL
almost exclusively (E1, validation confusion matrix, run 2026-09-12).
**Decision:** Replace cross-entropy with focal loss (gamma=2) in the training
loop to concentrate gradient signal on the minority UP/DOWN classes.
**Status:** Implemented
**Commits:** a3f9c1e (L. Palou), b7e2201 (L. Palou)
