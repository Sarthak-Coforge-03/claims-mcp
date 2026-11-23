#!/usr/bin/env bash
# PostToolUse hook: after Claude edits a Python file, run the test suite.
# Failures are fed back to Claude (exit 2) so it sees red tests immediately.

edited_file=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')

case "$edited_file" in
  *.py) ;;
  *) exit 0 ;;
esac

cd "$CLAUDE_PROJECT_DIR" || exit 0

if ! test_output=$(uv run pytest -q 2>&1); then
  echo "Tests failed after editing $edited_file:" >&2
  echo "$test_output" | tail -n 40 >&2
  exit 2
fi

exit 0
