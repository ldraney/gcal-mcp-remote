#!/bin/bash
# Prevent direct commits/pushes on main/master
# Uses command-boundary matching to avoid false positives on filenames/arguments
input=$(cat)
tool_input=$(echo "$input" | jq -r '.tool_input.command // ""')

# Match git commit/push only at command boundaries (start of line, after &&, ;, or |)
if ! echo "$tool_input" | grep -qE '(^|&&|;|\|)\s*git\s+(commit|push)'; then
  exit 0
fi

cwd=$(echo "$input" | jq -r '.cwd // empty')
branch=$(cd "${cwd:-.}" 2>/dev/null && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

if [[ "$branch" == "main" || "$branch" == "master" ]]; then
  echo "Blocked: cannot commit/push directly on $branch. Use a feature branch." >&2
  exit 2
fi
exit 0
