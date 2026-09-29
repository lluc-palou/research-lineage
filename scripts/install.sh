#!/usr/bin/env bash
# Symlinks skill/report-decision-framework into ~/.claude/skills/ so this
# repo stays the single source of truth for the skill's content. Editing
# the repo edits what Claude Code loads, no copy step, no drift.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_SRC="${REPO_ROOT}/skill/report-decision-framework"
SKILL_DEST="${HOME}/.claude/skills/report-decision-framework"

mkdir -p "${HOME}/.claude/skills"

if [ -e "${SKILL_DEST}" ] || [ -L "${SKILL_DEST}" ]; then
  echo "Removing existing ${SKILL_DEST}"
  rm -rf "${SKILL_DEST}"
fi

ln -s "${SKILL_SRC}" "${SKILL_DEST}"
echo "Linked ${SKILL_DEST} -> ${SKILL_SRC}"
