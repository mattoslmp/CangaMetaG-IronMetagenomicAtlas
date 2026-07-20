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
command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }

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

# GitHub rejects individual blobs >=100 MB. Split any such optional archive or
# dataset into deterministic parts and retain a checksum for reconstruction.
python3 - <<'PY'
from __future__ import annotations

import hashlib
import math
from pathlib import Path

root = Path('.')
hard_limit = 100 * 1024 * 1024
part_size = 90 * 1024 * 1024
large_files = [
  path for path in root.rglob('*')
  if path.is_file()
  and '.git' not in path.parts
  and '.part' not in path.name
  and path.stat().st_size >= hard_limit
]

for path in large_files:
  size = path.stat().st_size
  count = math.ceil(size / part_size)
  digest = hashlib.sha256()
  print(f'Splitting {path} ({size / 1024 / 1024:.2f} MB) into {count} parts...')
  with path.open('rb') as source:
    for number in range(1, count + 1):
      data = source.read(part_size)
      if not data:
        raise RuntimeError(f'Unexpected end of file while splitting {path}')
      digest.update(data)
      part = path.with_name(f'{path.name}.part{number:03d}-of-{count:03d}')
      part.write_bytes(data)
    if source.read(1):
      raise RuntimeError(f'Unwritten data remains for {path}')
  path.with_name(path.name + '.sha256').write_text(
    f'{digest.hexdigest()}  {path.name}\n', encoding='utf-8'
  )
  path.unlink()

oversized = [
  path for path in root.rglob('*')
  if path.is_file() and '.git' not in path.parts and path.stat().st_size >= hard_limit
]
if oversized:
  for path in oversized:
    print(f"ERROR: {path} remains above GitHub's 100 MB limit")
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
