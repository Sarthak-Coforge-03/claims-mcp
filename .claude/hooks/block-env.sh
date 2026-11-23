#!/usr/bin/env bash
# PreToolUse hook: blocks any tool call that touches a .env file (.env, .env.local, ...).
# .env.example is allowed because it holds no secrets.
# Exit code 2 tells Claude Code to block the call and show stderr to Claude.

hook_input=$(cat)

# Every field that can name a file: file tools use file_path/path/pattern, Bash uses command.
text_to_check=$(echo "$hook_input" | jq -r '[.tool_input.file_path, .tool_input.path, .tool_input.pattern, .tool_input.command] | map(select(. != null)) | join(" ")')

# Remove the allowed template first, then look for any remaining ".env" reference.
text_without_example=$(echo "$text_to_check" | sed 's/\.env\.example//g')

if echo "$text_without_example" | grep -Eq '\.env([^A-Za-z0-9_]|$)'; then
  echo "Blocked by .claude/hooks/block-env.sh: .env files hold secrets and must not be read or edited. Use .env.example instead." >&2
  exit 2
fi

exit 0
