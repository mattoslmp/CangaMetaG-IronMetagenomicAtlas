# CangaMetaG Iron Metagenomic Atlas

Interactive Streamlit atlas and reproducibility repository for the manuscript:

**An iron metagenomic atlas reveals biogeochemical cycling potential in Amazonian lateritic lake sediments**

**Authors:** Leandro de Mattos Pereira; José Augusto Pires Bittencourt; Vitor Cirilo Araujo Santos; Ronnie Alves; Eder Pires; Prafulla Kumar Sahoo; José Tasso Felix Guimarães; Bruno Garcia Simões; Renato R. Moreira-Oliveira; Guilherme Oliveira; Gisele Lopes Nunes  
**Affiliation:** Instituto Tecnológico Vale, Belém, PA, Brazil  
**Corresponding author:** Gisele Lopes Nunes — gisele.nunes@itv.org  
**Target journal:** *The ISME Journal*  
**Article type:** Original Article  
**Manuscript date:** 19 July 2026

## Abstract

Amazonian lateritic lakes over ferruginous canga are seasonally fluctuating, metal-rich sedimentary systems in which microbial contributions to redox and nutrient cycling remain insufficiently resolved. We used shotgun metagenomics to characterize sediment microbial communities from Amendoim, Violão, Três Irmãs and Três Irmãs Adjacent lakes across dry and rainy periods. Coding-sequence-based profiles revealed diverse bacterial and archaeal assemblages with a large unclassified fraction, supporting the presence of underexplored microbial diversity. Taxonomic contrasts highlighted lake- and season-associated shifts involving methanogenic, ammonia-oxidizing and anaerobic sediment lineages, whereas NMDS indicated partial community overlap and RDA linked genus-level variation to Fe2O3, Al2O3, SiO2, total carbon, loss on ignition and trace-metal gradients. Functional reconstruction detected broad potential for carbon fixation, methane metabolism, nitrogen cycling, sulfur transformations, photosynthesis, anaerobic oxidative phosphorylation and iron metabolism. A curated KO-marker framework detected 171 of 195 biogeochemical biomarkers and 132 iron-associated KOs, and descriptive cross-study contrasts separated Amazonian canga-lake signals from external iron-rich records. Amazonian-positive contrasts emphasized methanogenesis, denitrification, DMSO-linked respiration and iron-reduction or heme-linked markers, whereas external records more strongly represented phototrophy, methylotrophy, siderophore-related acquisition and oxidative iron handling. We recovered 50 non-redundant MAGs spanning medium- to high-quality genome bins, including Acidobacteria, Dehalococcoidia, Nitrospirales, Burkholderiales, Bathyarchaeia, Thermoplasmatota and Methanoperedens-related lineages. These results provide a genome-resolved iron metagenomic atlas for tropical lateritic lake sediments and a foundation for testing how seasonal hydrology modulates microbial biogeochemical functions in ferruginous Amazonian ecosystems.

## Repository contents

The repository is intended to contain the complete application supplied with the article package, including:

- the Streamlit application (`app.py`);
- reusable Python modules (`src/`);
- independent analysis and figure-generation scripts (`scripts/`);
- processed taxonomic, functional, environmental, MAG, antiSMASH and KEGG/KEMET inputs (`data/`);
- Supplementary Tables 1–11 and audit tables (`tables/`);
- the main and supplementary publication figures in PNG, PDF and SVG (`outputs/`);
- manuscript-linked documentation (`docs/`);
- provenance, checksums and validation records (`00_Provenance/`, `Checksums/`, `validation/`);
- figure-to-script and section-to-script manifests.

## RDA consistency with the manuscript

The default interactive RDA follows the same workflow as `scripts/consolidate_final_publication.py`:

1. read `data/resultado.cds.otu.tab`, `data/resultado.cds.tax.tab` and `data/fiqui2.xlsx`;
2. map IMG/JGI identifiers to the 20 lake-season samples;
3. pool dry and rainy counts into ten physicochemical sampling positions;
4. aggregate CDS counts at genus level, including the unclassified fraction;
5. retain the 80 genera with the largest total counts;
6. apply a Hellinger transformation;
7. average physicochemical replicates by `SampleMM`;
8. consider predictors in this order: `Fe2O3`, `SiO2`, `Al2O3`, `TOT/C`, `TOT/S`, `LOI`, `V`, `Cu`, `Pb`, `Zr`, `Ce`;
9. remove near-zero-variance predictors and require absolute pairwise correlation below 0.92;
10. retain at most six predictors;
11. standardize predictors and fit the constrained model;
12. evaluate the global pseudo-F statistic with 999 permutations and random seed 42.

The article model retains:

```text
Fe2O3, SiO2, Al2O3, TOT/S, Cu, Pb
```

Cu and Pb are the retained trace-metal predictors. The expected model statistics are:

```text
n = 10 sampling positions
constrained R2 = 0.6605827831733051
pseudo-F = 0.9731132518103761
permutation P = 0.534
```

The static RDA-containing files in `outputs/final_publication_figures/` and `outputs/app_supplementary_figures/` must be copied directly from the article submission package. This applies to Main Figures 4 and 5 and Supplementary Figure 17.

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
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the app

```bash
streamlit run app.py --server.port 8502 --server.address 0.0.0.0
```

No-root launcher:

```bash
bash run_app_no_root.sh \
  --server.port 8502 \
  --server.address 0.0.0.0 \
  --server.headless true
```

Administrator credentials are optional and must be provided through environment variables. Never commit credentials.

```bash
export CANGAMETAG_ADMIN_USER='admin'
export CANGAMETAG_ADMIN_PASSWORD='replace-with-a-strong-password'
```

## Reproduce the RDA

```bash
python scripts/consolidate_final_publication.py
```

The generated source tables are written under `data/final_publication_derived/`. Domain-separated RDA panels in Main Figures 4 and 5 are generated with:

```bash
python scripts/build_taxonomy_palette.py
python scripts/generate_final_domain_taxonomy_figures.py
```

## Reproduce all main and supplementary figures

```bash
bash scripts/final_publication_figures/run_all_portable.sh
```

The authoritative figure-to-input-to-script mapping is stored in:

```text
FIGURE_SCRIPT_REPRODUCIBILITY_MANIFEST.md
Final_Figures_and_Scripts/FIGURE_SCRIPT_REPRODUCIBILITY_MANIFEST.md
Final_Figures_and_Scripts/figure_script_manifest.csv
Final_Figures_and_Scripts/final_figure_script_manifest.csv
data/figure_script_manifest.csv
data/final_figure_script_manifest.csv
```

See `scripts/README.md` and `RUN_APP_AND_REPRODUCE_FIGURES.md` for independent commands.

## Validation

```bash
python -m compileall -q app.py src scripts
bash -n run_app_no_root.sh
python scripts/consolidate_final_publication.py
python scripts/validate_canonical_figure_bundle.py
python scripts/validate_runtime_permissions.py
```

## Data availability

Raw reads are deposited under ENA study `ERP137391` with runs `ERR9980190–ERR9980209`. Binned-metagenome analyses are available as `ERZ29768260–ERZ29768309`.

## Publishing the complete package

The complete corrected package contains `scripts/publish_repository.sh`, which synchronizes every application file to this public repository while preserving Git history and automatically splits files that exceed GitHub's 100 MB per-file limit. Full instructions are in `PUBLISH_TO_GITHUB.md`.

## Citation

Use the metadata in `CITATION.cff` when citing the software and repository.
