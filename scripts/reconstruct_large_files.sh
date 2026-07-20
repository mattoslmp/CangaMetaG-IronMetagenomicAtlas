#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
restored=0

while IFS= read -r first_part; do
  base="${first_part%.part001-of-*}"
  mapfile -t parts < <(find "$(dirname "$base")" -maxdepth 1 -type f -name "$(basename "$base").part*-of-*" | sort -V)
  if (( ${#parts[@]} == 0 )); then
    continue
  fi
  echo "Restoring $base from ${#parts[@]} parts..."
  cat "${parts[@]}" > "$base"
  checksum_file="${base}.sha256"
  if [[ -f "$checksum_file" ]]; then
    (cd "$(dirname "$base")" && sha256sum -c "$(basename "$checksum_file")")
  fi
  restored=$((restored + 1))
done < <(find "$ROOT" -type f -name '*.part001-of-*' | sort)

if (( restored == 0 )); then
  echo "No split large files were found."
else
  echo "Restored $restored split file(s)."
fi
