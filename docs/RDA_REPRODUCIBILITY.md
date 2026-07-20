# RDA reproducibility

## Scientific model

The manuscript and the default interactive application use a genus-level redundancy analysis based on CDS taxonomic counts and sediment physicochemistry.

The workflow:

1. maps IMG/JGI CDS sample identifiers to the 20 lake-season samples;
2. aggregates dry and rainy samples by the ten physicochemical sampling positions;
3. aggregates CDS counts by genus and retains the 80 genera with the largest total counts;
4. applies a Hellinger transformation to the community matrix;
5. averages physicochemical replicates by `SampleMM`;
6. considers predictors in the fixed order `Fe2O3`, `SiO2`, `Al2O3`, `TOT/C`, `TOT/S`, `LOI`, `V`, `Cu`, `Pb`, `Zr`, `Ce`;
7. removes near-zero-variance predictors;
8. retains a predictor only when its absolute Pearson correlation with every already retained predictor is below 0.92;
9. stops after six predictors;
10. standardizes predictors and fits the constrained model;
11. evaluates the global pseudo-F statistic with 999 permutations using random seed 42.

With the packaged data, the retained predictors are:

```text
Fe2O3, SiO2, Al2O3, TOT/S, Cu, Pb
```

Cu and Pb are the trace-metal variables retained in the final model.

## Canonical scripts

- `scripts/consolidate_final_publication.py`: exact all-community genus RDA used for the article Supplementary Figure 17 source tables and the default interactive model.
- `scripts/generate_final_domain_taxonomy_figures.py`: Bacteria- and Archaea-separated taxonomy, NMDS and RDA panels used in Main Figures 4 and 5.
- `scripts/RDA_Taxon_env_Gi.R`: original R workflow preserved for provenance.
- `scripts/validate_article_rda_consistency.py`: deterministic validation against the article reference values and figure checksums.

## Inputs

```text
data/resultado.cds.otu.tab
data/resultado.cds.tax.tab
data/fiqui2.xlsx
```

## Expected article-wide result

```text
n positions = 10
constrained R2 = 0.6605827831733045
pseudo-F = 0.9731132518103737
permutation P = 0.534
predictors = Fe2O3, SiO2, Al2O3, TOT/S, Cu, Pb
```

## Validation

From the repository root:

```bash
python scripts/validate_article_rda_consistency.py
```

The command writes `validation/RDA_CONSISTENCY_REPORT.json` and exits with a non-zero status when the model, required files or canonical figure hashes do not match the article reference.

## Interactive application

The RDA interface in `app.py` uses the same sample mapping, genus aggregation, top-80 filter, Hellinger transformation, predictor order, collinearity threshold, six-variable cap, standardization, constrained fit and 999-permutation test as `scripts/consolidate_final_publication.py`.

Users may explore other taxonomic levels or manually change predictors, but the default genus-level configuration reproduces the article model.
