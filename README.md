# CangaMetaG Iron Metagenomic Atlas

Reproducibility repository and interactive Streamlit atlas for the manuscript:

**Iron-rich Amazonian lateritic lake sediments harbor diverse microbial communities with biogeochemical potential relevant to carbon and methane cycling**

**Authors:** Leandro de Mattos Pereira; José Augusto Pires Bittencourt; Vitor Cirilo Araujo Santos; Ronnie Alves; Eder Pires; Prafulla Kumar Sahoo; José Tasso Felix Guimarães; Bruno Garcia Simões; Renato R. Moreira-Oliveira; Guilherme Oliveira; Gisele Lopes Nunes  
**Affiliation:** Instituto Tecnológico Vale, Belém, PA, Brazil  
**Correspondence:** Gisele Lopes Nunes — gisele.nunes@itv.org; Leandro de Mattos Pereira — leandro.pereira@pq.itv.org  
**Target journal:** *The ISME Journal*  
**Article type:** Original Article  
**Manuscript date:** 19 July 2026

## Scope

The repository contains the complete Streamlit application, independent analysis and figure-generation scripts, processed source data, all supplementary tables, publication figures, validation records and figure-to-script manifests associated with the Amazonian lateritic-lake sediment metagenomic atlas.

The app covers taxonomic profiles, alpha and beta diversity, NMDS, redundancy analysis, KO biomarkers, differential abundance, KEGG/KEMET module completeness, FeGenie summaries, MAG quality and taxonomy, antiSMASH biosynthetic gene clusters, ST8 comparisons and environmental integration.


## Installation

### Conda

```bash
git clone https://github.com/mattoslmp/CangaMetaG-IronMetagenomicAtlas.git
cd CangaMetaG-IronMetagenomicAtlas
conda env create -f environment.yml
conda activate cangametag-iron-atlas
```

### Python virtual environment

```bash
git clone https://github.com/mattoslmp/CangaMetaG-IronMetagenomicAtlas.git
cd CangaMetaG-IronMetagenomicAtlas
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the app

```bash
streamlit run app.py --server.port 8502 --server.address 0.0.0.0
```

Portable no-root launch:

```bash
bash run_app_no_root.sh --server.port 8502 --server.address 0.0.0.0 --server.headless true
```

Administrator credentials are optional and must be supplied through environment variables. Never commit passwords or tokens.

```bash
export CANGAMETAG_ADMIN_USER='admin'
export CANGAMETAG_ADMIN_PASSWORD='replace-with-a-strong-password'
```

## Reproduce and validate the RDA

Validate the default interactive RDA against the article reference statistics:

```bash
python scripts/validate_article_rda_consistency.py
```

Regenerate the article-wide RDA source tables and standalone RDA panel:

```bash
python scripts/consolidate_final_publication.py
```

Regenerate the domain-separated taxonomic profiles and RDA panels used in Main Figures 4 and 5:

```bash
python scripts/build_taxonomy_palette.py
python scripts/generate_final_domain_taxonomy_figures.py
```

Expected synchronized outputs include:

```text
outputs/final_publication_figures/Figure4_taxonomic_bacteria_genus_profiles.{png,pdf,svg}
outputs/final_publication_figures/Figure5_taxonomic_archaea_genus_profiles.{png,pdf,svg}
outputs/final_publication_figures/SupplementaryFigure17_RDA_and_physicochemical_heatmap.{png,pdf,svg}
outputs/app_supplementary_figures/SupplementaryFigure17_RDA_and_physicochemical_heatmap.{png,pdf,svg}
```

## Reproduce all main and supplementary figures

Run the portable validation and generation workflow:

```bash
bash scripts/final_publication_figures/run_all_portable.sh
```

Individual scripts can also be run separately. The authoritative mapping of each figure to its input data, script, command, dependencies and output files is provided in:

```text
FIGURE_SCRIPT_REPRODUCIBILITY_MANIFEST.md
Final_Figures_and_Scripts/figure_script_manifest.csv
Final_Figures_and_Scripts/final_figure_script_manifest.csv
scripts/README.md
```

## Supplementary tables

All Supplementary Tables 1-11 are stored in `tables/submission/` and mirrored in `tables/`. The app loads these tables through the database layer without modifying their source values.

## Validation

```bash
python -m compileall -q app.py src scripts
bash -n run_app_no_root.sh
python scripts/validate_article_rda_consistency.py
python scripts/validate_canonical_figure_bundle.py
python scripts/validate_runtime_permissions.py
```

The RDA validation must confirm:

```text
n = 10 sampling positions
predictors = Fe2O3, SiO2, Al2O3, TOT/S, Cu, Pb
constrained R2 approximately 0.661
pseudo-F approximately 0.97
permutation P approximately 0.534
```

## Data availability

Raw sequencing data are available under ENA study `ERP137391`, with run accessions `ERR9980190-ERR9980209`. Binned-metagenome analyses are available as `ERZ29768260-ERZ29768309`. Processed source tables and supplementary materials required by the application and figure scripts are included in this repository.

Large native antiSMASH report directories and sequence collections are retained in the complete application package. Summary tables and all manuscript-level results are stored directly in the repository.

## Publishing the complete package

The GitHub-ready package stores the optional native antiSMASH archive in numbered parts below GitHub's 100 MB per-file limit. Publishing and reconstruction instructions are provided in `PUBLISH_TO_GITHUB.md` and `scripts/reconstruct_large_files.sh`.

## Citation

Citation metadata are provided in `CITATION.cff`.
