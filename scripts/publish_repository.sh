#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE="${GITHUB_REMOTE:-https://github.com/mattoslmp/CangaMetaG-IronMetagenomicAtlas.git}"
BRANCH="${GITHUB_BRANCH:-main}"
COMMIT_MESSAGE="${GITHUB_COMMIT_MESSAGE:-Publish CangaMetaG app, scripts, data and publication assets}"
WORKDIR="$(mktemp -d -t cangametag-publish-XXXXXX)"
trap 'rm -rf "$WORKDIR"' EXIT

command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
command -v rsync >/dev/null || { echo "rsync is required" >&2; exit 1; }

echo "Cloning $REMOTE ($BRANCH)..."
git clone --branch "$BRANCH" --single-branch "$REMOTE" "$WORKDIR/repository"

rsync -a --delete \
  --exclude='.git/' \
  --exclude='.venv/' \
  --exclude='venv/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='.streamlit/secrets.toml' \
  --exclude='.env' \
  "$ROOT/" "$WORKDIR/repository/"

cd "$WORKDIR/repository"

python - <<'PY'
from pathlib import Path
limit = 100 * 1024 * 1024
oversized = [(p.stat().st_size, p) for p in Path('.').rglob('*') if p.is_file() and '.git' not in p.parts and p.stat().st_size >= limit]
if oversized:
  for size, path in sorted(oversized, reverse=True):
    print(f"ERROR: {path} is {size / 1024 / 1024:.2f} MB and exceeds GitHub's file limit")
  raise SystemExit(1)
print('GitHub file-size validation: PASS')
PY

git add -A
if git diff --cached --quiet; then
  echo "No repository changes to publish."
  exit 0
fi

git commit -m "$COMMIT_MESSAGE"
git push origin "$BRANCH"
echo "Repository published successfully: $REMOTE"
