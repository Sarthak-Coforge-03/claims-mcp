#!/usr/bin/env bash
# PostToolUse hook: after Claude edits a Python file, format it and lint it with ruff.
#   1. `ruff format`        rewrites the file to the project's formatting style
#   2. `ruff check --fix`   auto-fixes what it safely can (e.g. import order, unused imports)
# Anything ruff cannot fix is fed back to Claude (exit 2) so it fixes it straight away.
# Runs on the host for speed (same ruff version as the container, pinned in uv.lock).

edited_file=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')

case "$edited_file" in
  *.py) ;;
  *) exit 0 ;;
esac

cd "$CLAUDE_PROJECT_DIR" || exit 0

uv run ruff format --quiet "$edited_file" >/dev/null 2>&1

if ! lint_output=$(uv run ruff check --fix --quiet "$edited_file" 2>&1); then
  echo "[ruff] Lint problems ruff could not auto-fix in $edited_file:" >&2
  echo "$lint_output" | tail -n 40 >&2
  exit 2
fi

exit 0
