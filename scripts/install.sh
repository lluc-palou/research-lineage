#!/usr/bin/env bash
# Symlinks skill/report-decision-framework into ~/.claude/skills/ so this
# repo stays the single source of truth for the skill's content. Editing
# the repo edits what Claude Code loads, no copy step, no drift.
#
# Refuses to replace a real directory (a hand-made copy may hold unsaved
# edits) and refuses to fall back to a copy, which Git Bash on Windows does
# silently for `ln -s` unless native symlinks are forced. On Windows without
# Developer Mode, use scripts/install.ps1 instead (directory junction).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_SRC="${REPO_ROOT}/skill/report-decision-framework"
SKILL_DEST="${HOME}/.claude/skills/report-decision-framework"

# Forces a real symlink under MSYS/Git Bash (fails instead of copying)
export MSYS="${MSYS:-} winsymlinks:nativestrict"

mkdir -p "${HOME}/.claude/skills"

if [ -L "${SKILL_DEST}" ]; then
  echo "Replacing existing link ${SKILL_DEST}"
  rm "${SKILL_DEST}"
elif [ -e "${SKILL_DEST}" ]; then
  echo "ERROR: ${SKILL_DEST} exists and is not a symlink." >&2
  echo "Move or delete it manually, then re-run this script." >&2
  exit 1
fi

if ! ln -s "${SKILL_SRC}" "${SKILL_DEST}" || [ ! -L "${SKILL_DEST}" ]; then
  echo "ERROR: could not create a symlink at ${SKILL_DEST}." >&2
  echo "On Windows, enable Developer Mode or run scripts/install.ps1." >&2
  exit 1
fi

echo "Linked ${SKILL_DEST} -> ${SKILL_SRC}"
