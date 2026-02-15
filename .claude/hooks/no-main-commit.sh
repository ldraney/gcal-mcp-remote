#!/bin/bash
# Prevent direct commits on main/master
input=$(cat)
tool_input=$(echo "$input" | jq -r '.tool_input.command // ""')

# Only check git commit commands
if ! echo "$tool_input" | grep -qE 'git.*commit'; then
  exit 0
fi

branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if [[ "$branch" == "main" || "$branch" == "master" ]]; then
  echo "Blocked: cannot commit directly on $branch. Use a feature branch." >&2
  exit 2
fi
exit 0
