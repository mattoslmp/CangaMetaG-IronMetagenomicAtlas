#!/usr/bin/env bash
set -euo pipefail
PACKAGE_KIND="${1:-APP}"
case "$PACKAGE_KIND" in
  APP|app) STEM="CangaMetaG_App_Final.zip"; COUNT=29 ;;
  ARTICLE|article) STEM="CangaMetaG_Article_Final.zip"; COUNT=47 ;;
  *) echo "Usage: $0 APP|ARTICLE" >&2; exit 2 ;;
esac
DIR="${2:-.}"
mapfile -t parts < <(find "$DIR" -maxdepth 1 -type f -name "$STEM.part*-of-$(printf '%03d' "$COUNT")" | sort)
[[ ${#parts[@]} -eq $COUNT ]] || { echo "Expected $COUNT parts; found ${#parts[@]}" >&2; exit 1; }
cat "${parts[@]}" > "$DIR/$STEM"
( cd "$DIR" && sha256sum -c "$STEM.sha256" )
unzip -t "$DIR/$STEM"
echo "Validated: $DIR/$STEM"
