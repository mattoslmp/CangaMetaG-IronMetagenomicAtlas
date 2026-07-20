# Publishing the complete repository to GitHub

The repository is designed for:

```text
https://github.com/mattoslmp/CangaMetaG-IronMetagenomicAtlas
```

The package contains the complete Streamlit app, independent scripts, processed source data, Supplementary Tables 1–11, publication figures, manifests and validation records. GitHub rejects individual files larger than 100 MB. During publication, `scripts/publish_repository.sh` automatically divides any such file into deterministic parts below 90 MB and writes a SHA-256 checksum. The included reconstruction script restores the original files when needed.

## Requirements

```bash
sudo apt update
sudo apt install -y git rsync python3
```

Configure Git once:

```bash
git config --global user.name "Leandro de Mattos Pereira"
git config --global user.email "YOUR_GITHUB_EMAIL"
```

Authentication can use a GitHub personal access token, SSH key or GitHub CLI.

## Publish from the extracted package

From the repository root:

```bash
bash scripts/publish_repository.sh
```

The script clones the current `main` branch, synchronizes the complete package while preserving the remote history, automatically splits files that exceed GitHub's 100 MB limit, verifies the resulting tree, commits the repository contents and pushes to `main`.

To use SSH:

```bash
GITHUB_REMOTE='git@github.com:mattoslmp/CangaMetaG-IronMetagenomicAtlas.git' \
  bash scripts/publish_repository.sh
```

## Restore split large files

After cloning the repository:

```bash
bash scripts/reconstruct_large_files.sh
```

This command finds every numbered split-file series, concatenates the parts and verifies the SHA-256 checksum before restoring the original file.

## Validate after cloning

```bash
python -m compileall -q app.py src scripts
bash -n run_app_no_root.sh
python scripts/validate_article_rda_consistency.py
python scripts/validate_canonical_figure_bundle.py
python scripts/validate_runtime_permissions.py
```
