#!/usr/bin/env bash
set -euo pipefail

raw_input="$(cat)"
if [[ -z "${raw_input}" ]]; then
  exit 0
fi

normalized="$(printf "%s" "$raw_input" | tr '[:upper:]' '[:lower:]')"

if ! printf "%s" "$normalized" | grep -Eq "\\bgit[[:space:]]+commit\\b|\\bgit[[:space:]]+push\\b|\\bgh[[:space:]]+pr[[:space:]]+create\\b"; then
  exit 0
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"

python_cmd="python"
if [[ -x "$repo_root/venv/bin/python" ]]; then
  python_cmd="$repo_root/venv/bin/python"
fi

if (cd "$repo_root" && "$python_cmd" manage.py test core.tests); then
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"Test gate passed: manage.py test core.tests"}}\n'
  exit 0
fi

printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Blocked: tests failed (manage.py test core.tests). Fix tests before commit/push/PR create."}}\n'
exit 0
