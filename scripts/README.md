# Independent analysis and figure scripts

All commands below are run from the repository root after activating the environment defined in `environment.yml` or installing `requirements.txt`.

## RDA, taxonomy and ordination

### Article-wide genus RDA and publication figures

```bash
python scripts/consolidate_final_publication.py
```

This is the canonical article-wide RDA implementation. It uses `data/resultado.cds.otu.tab`, `data/resultado.cds.tax.tab` and `data/fiqui2.xlsx`. The default model retains `Fe2O3`, `SiO2`, `Al2O3`, `TOT/S`, `Cu` and `Pb` and uses 999 permutations with seed 42.

### Domain-separated Main Figures 2–5 and Supplementary Figure 17 panels

```bash
python scripts/build_taxonomy_palette.py
python scripts/generate_final_domain_taxonomy_figures.py
```

### Original R workflow

```bash
Rscript scripts/RDA_Taxon_env_Gi.R
```

The R script is retained for provenance. Its package and input requirements are described in `docs/RDA_REPRODUCIBILITY.md`.

### Deterministic RDA validation

```bash
python scripts/validate_article_rda_consistency.py
```

## Taxonomic supplementary figures

```bash
python scripts/generate_taxonomy_supplementary_figures.py
python scripts/generate_core_taxonomy_overlap_figure.py
python scripts/final_taxonomy_dashboard_update.py
python scripts/validate_taxonomy_adendum.py
```

## Rarefaction and alpha diversity

```bash
python scripts/final_publication_figures/06_recalculate_rarefaction_alpha_32999.py
```

## KO biomarkers and environmental contrasts

```bash
python scripts/generate_bidirectional_environment_contrast_figures.py
python scripts/rebuild_st8_final_exports.py
```

## KEGG/KEMET module completeness

```bash
python scripts/build_kemet_outputs.py
python scripts/generate_kegg_module_completeness_heatmaps_green_blue_red.py
```

## MAG, FeGenie and antiSMASH integration

```bash
python scripts/parse_antismash_bgc_table.py
python scripts/integrate_kemet_antismash.py
python scripts/generate_supplementary_figure5_mag_labels.py
```

The parser can use native antiSMASH directories when mounted locally. The manuscript-level region and summary tables are included in `data/` and the supplementary workbooks.

## Maps and workflow diagrams

```bash
python scripts/generate_amazon_coordinate_figure.py
python scripts/generate_atlas_workflow_figure.py
```

## Figure synchronization and visual quality control

```bash
python scripts/09_mandatory_figure_corrections_30Jun2026.py
python scripts/final_visual_sync.py
python scripts/regenerate_sync_final_figures.py
python scripts/validate_canonical_figure_bundle.py
```

## Full portable execution

```bash
bash scripts/final_publication_figures/run_all_portable.sh
```

The portable workflow begins with input validation, recalculates the fixed-depth rarefaction and alpha-diversity results, regenerates the canonical figure set and runs final checks.

## Complete figure-to-script mapping

The authoritative input, command, dependency, random-seed and output mapping for every main and supplementary figure is provided in:

```text
FIGURE_SCRIPT_REPRODUCIBILITY_MANIFEST.md
Final_Figures_and_Scripts/figure_script_manifest.csv
Final_Figures_and_Scripts/final_figure_script_manifest.csv
data/final_figure_script_manifest.csv
```
