#!/usr/bin/env bash
# Prepare the shared tool directory that figure-check.mjs (explainer skill)
# needs for PR figures: playwright, vlmkit and mermaid. Installed once under
# the user's cache so a PR does not add node_modules to the repository.
#
# Usage: setup.sh            # prints the tool directory on stdout
set -euo pipefail

TOOLS_DIR="${PR_DESCRIPTION_TOOLS:-${XDG_CACHE_HOME:-${HOME}/.cache}/pr-description}"
mkdir -p "${TOOLS_DIR}/work"

if [[ ! -f "${TOOLS_DIR}/package.json" ]]; then
  (cd "${TOOLS_DIR}" && npm init -y >/dev/null)
fi
if [[ ! -d "${TOOLS_DIR}/node_modules/mermaid" || ! -d "${TOOLS_DIR}/node_modules/playwright" ]]; then
  (cd "${TOOLS_DIR}" && npm i -D --no-audit --no-fund \
    @mizchi/vlmkit @mizchi/vlmkit-anim marked playwright mermaid >&2)
  (cd "${TOOLS_DIR}" && npx playwright install chromium >&2)
fi
echo "${TOOLS_DIR}"
