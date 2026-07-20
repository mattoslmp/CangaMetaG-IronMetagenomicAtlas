#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE="${GITHUB_REMOTE:-https://github.com/mattoslmp/CangaMetaG-IronMetagenomicAtlas.git}"
BRANCH="${GITHUB_BRANCH:-main}"
COMMIT_MESSAGE="${GITHUB_COMMIT_MESSAGE:-Deposit complete original app with article-consistent RDA}"
WORKDIR="$(mktemp -d -t cangametag-publish-XXXXXX)"
trap 'rm -rf "$WORKDIR"' EXIT

for command in git git-lfs rsync; do
  command -v "$command" >/dev/null || {
    echo "$command is required" >&2
    echo "Ubuntu: sudo apt update && sudo apt install -y git git-lfs rsync" >&2
    exit 1
  }
done

git lfs install

echo "Cloning $REMOTE ($BRANCH)..."
git clone --branch "$BRANCH" --single-branch "$REMOTE" "$WORKDIR/repository"

# Preserve the remote .git history, but replace the working tree with the exact
# application directory from which this script is executed.
find "$WORKDIR/repository" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
rsync -a \
  --exclude='.git/' \
  --exclude='.venv/' \
  --exclude='venv/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='.streamlit/secrets.toml' \
  --exclude='.env' \
  "$ROOT/" "$WORKDIR/repository/"

cd "$WORKDIR/repository"

# Preserve the original filename and path of the only application file above
# GitHub's normal 100 MB blob limit.
git lfs track "data/kegg_modules/raw_uploaded_archives/antismash(1)(1).zip"
git add .gitattributes
git add -A

if git diff --cached --quiet; then
  echo "No repository changes to publish."
  exit 0
fi

git commit -m "$COMMIT_MESSAGE"
git push origin "$BRANCH"
echo "Complete application published successfully: $REMOTE"
