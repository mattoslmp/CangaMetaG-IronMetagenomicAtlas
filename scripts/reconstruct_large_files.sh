#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PART_DIR="$ROOT/data/kegg_modules/raw_uploaded_archives"
BASENAME="antismash(1)(1).zip"
CHECKSUM_FILE="$PART_DIR/${BASENAME}.sha256"

mapfile -t parts < <(find "$PART_DIR" -maxdepth 1 -type f -name "${BASENAME}.part*-of-*" | sort -V)
if (( ${#parts[@]} == 0 )); then
  echo "No split archive parts were found."
  exit 0
fi

output="$PART_DIR/$BASENAME"
cat "${parts[@]}" > "$output"
if [[ -f "$CHECKSUM_FILE" ]]; then
  (cd "$PART_DIR" && sha256sum -c "$(basename "$CHECKSUM_FILE")")
fi
echo "Restored: $output"
