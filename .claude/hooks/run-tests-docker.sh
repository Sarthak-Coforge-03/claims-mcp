#!/usr/bin/env bash
# PostToolUse hook: after Claude edits a Python file, run the test suite inside the Docker
# dev container (same environment CI will use). Runs alongside run-tests.sh (host tests).
# Failures are fed back to Claude (exit 2) so it sees red tests immediately.

edited_file=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')

case "$edited_file" in
  *.py) ;;
  *) exit 0 ;;
esac

cd "$CLAUDE_PROJECT_DIR" || exit 0

if ! docker info >/dev/null 2>&1; then
  echo "[docker] Docker isn't running — start Docker Desktop to run tests in the container." >&2
  exit 2
fi

if ! test_output=$(docker compose run --rm dev uv run pytest -q 2>&1); then
  echo "[docker] Tests failed in container after editing $edited_file:" >&2
  echo "$test_output" | tail -n 40 >&2
  exit 2
fi

exit 0
