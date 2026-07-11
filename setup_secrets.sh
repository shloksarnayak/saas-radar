#!/usr/bin/env bash
# One-shot setup: pushes all required secrets to the saas-radar GitHub repo and
# triggers the first workflow run. Requires: gh CLI installed, and .secrets.env
# filled in (copy from .secrets.env.example next to this script) including a
# GH_TOKEN (repo + workflow scopes) — used directly via env var rather than
# `gh auth login`, since login's default scope check is stricter than what
# actual API calls need.
set -euo pipefail
cd "$(dirname "$0")"

REPO="shloksarnayak/saas-radar"

if [ ! -f .secrets.env ]; then
  echo "Missing .secrets.env — copy .secrets.env.example to .secrets.env and fill in values first." >&2
  exit 1
fi

set -a
source .secrets.env
set +a

if [ -z "${GH_TOKEN:-}" ]; then
  echo "Missing GH_TOKEN in .secrets.env (a GitHub token with repo + workflow scopes)." >&2
  exit 1
fi
export GH_TOKEN

required=(ANTHROPIC_API_KEY GMAIL_ADDRESS GMAIL_APP_PASSWORD DIGEST_TO_ADDRESS)
missing=()
for var in "${required[@]}"; do
  if [ -z "${!var:-}" ]; then
    missing+=("$var")
  fi
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "Missing values in .secrets.env: ${missing[*]}" >&2
  exit 1
fi

echo "Pushing secrets to $REPO..."
for var in "${required[@]}"; do
  gh secret set "$var" --body "${!var}" -R "$REPO"
  echo "  set $var"
done

optional=(PRODUCTHUNT_TOKEN)
for var in "${optional[@]}"; do
  if [ -n "${!var:-}" ]; then
    gh secret set "$var" --body "${!var}" -R "$REPO"
    echo "  set $var (optional)"
  else
    echo "  skipped $var (optional, not set)"
  fi
done

echo "Triggering first workflow run..."
gh workflow run daily-scan.yml -R "$REPO"

echo "Done. Check progress at: https://github.com/$REPO/actions"
