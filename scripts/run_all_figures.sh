#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export MPLBACKEND=Agg

run() {
  echo
  echo "==> $*"
  "$@"
}

run python scripts/final_publication_figures/00_validate_final_inputs_and_outputs.py
run python scripts/build_taxonomy_palette.py
run python scripts/generate_final_domain_taxonomy_figures.py
run python scripts/final_publication_figures/06_recalculate_rarefaction_alpha_32999.py
run python scripts/consolidate_final_publication.py
run python scripts/regenerate_figure8_comparison_labels_v9.py
run python scripts/generate_supplementary_figure5_mag_labels.py
run python scripts/final_visual_sync.py
run python scripts/generate_core_taxonomy_overlap_figure.py
run python scripts/generate_atlas_workflow_figure.py
run python scripts/generate_bidirectional_environment_contrast_figures.py
run python scripts/generate_taxonomy_supplementary_figures.py
run python scripts/regenerate_module_figures_filtered_v9.py
run python scripts/normalize_all_figure_legibility_v9.py
run python scripts/validate_all_figures_v9.py

echo
printf 'All canonical figure stages completed successfully.\n'
