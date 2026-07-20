"""Canonical genus-level RDA used by the manuscript and default app view."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SAMPLE_MAP = {
  "Ga0540489": "AM.P1.D", "Ga0541010": "AM.P1.R", "Ga0541011": "AM.P2.D", "Ga0541012": "AM.P2.R",
  "Ga0541013": "TIA.P1.D", "Ga0541014": "TIA.P1.R", "Ga0541015": "TIA.P2.D", "Ga0541016": "TIA.P2.R",
  "Ga0541017": "TI.P1.D", "Ga0541018": "TI.P1.R", "Ga0541019": "TI.P2.D", "Ga0541020": "TI.P2.R",
  "Ga0541021": "TI.P3.D", "Ga0541022": "TI.P3.R", "Ga0541023": "TI.P4.D", "Ga0541024": "TI.P4.R",
  "Ga0541025": "VI.P1.D", "Ga0541026": "VI.P1.R", "Ga0541027": "VI.P2.D", "Ga0541028": "VI.P2.R",
}
SAMPLE_ORDER = [
  "AM.P1.D", "AM.P1.R", "AM.P2.D", "AM.P2.R",
  "TIA.P1.D", "TIA.P1.R", "TIA.P2.D", "TIA.P2.R",
  "TI.P1.D", "TI.P1.R", "TI.P2.D", "TI.P2.R", "TI.P3.D", "TI.P3.R", "TI.P4.D", "TI.P4.R",
  "VI.P1.D", "VI.P1.R", "VI.P2.D", "VI.P2.R",
]
PREFERRED_PREDICTORS = ["Fe2O3", "SiO2", "Al2O3", "TOT/C", "TOT/S", "LOI", "V", "Cu", "Pb", "Zr", "Ce"]


def clean_sample_name(column: str) -> str:
  token = str(column).split("_")[0]
  return SAMPLE_MAP.get(token, token)


def load_cds(data_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
  data = Path(data_dir)
  otu = pd.read_csv(data / "resultado.cds.otu.tab", sep="\t", index_col=0)
  otu.columns = [clean_sample_name(column) for column in otu.columns]
  otu = otu.reindex(columns=[column for column in SAMPLE_ORDER if column in otu.columns])
  otu = otu.apply(pd.to_numeric, errors="coerce").fillna(0)
  taxonomy = pd.read_csv(data / "resultado.cds.tax.tab", sep="\t", index_col=0)
  taxonomy.columns = [str(column).strip() for column in taxonomy.columns]
  for column in taxonomy.columns:
    taxonomy[column] = taxonomy[column].astype(str).str.strip().replace(
      {"nan": "Unclassified", "NA": "Unclassified", "": "Unclassified"}
    )
  return otu, taxonomy


def run_article_rda(
  otu: pd.DataFrame,
  taxonomy: pd.DataFrame,
  physicochemistry_path: str | Path,
  top_n: int = 80,
  correlation_threshold: float = 0.92,
  maximum_predictors: int = 6,
  permutations: int = 999,
  random_seed: int = 42,
) -> dict[str, Any]:
  shared = otu.index.intersection(taxonomy.index)
  genera = (
    taxonomy.loc[shared, "Genus"]
    .fillna("Unclassified")
    .astype(str)
    .str.strip()
    .replace({"": "Unclassified", "NA": "Unclassified", "nan": "Unclassified"})
  )
  matrix = otu.loc[shared].copy()
  matrix["Genus"] = genera
  genus_counts = matrix.groupby("Genus").sum(numeric_only=True)

  position_map = {column: ".".join(column.split(".")[:2]) for column in genus_counts.columns}
  position_counts = pd.DataFrame({
    position: genus_counts[[column for column, mapped in position_map.items() if mapped == position]].sum(axis=1)
    for position in sorted(set(position_map.values()))
  }).T
  position_counts = position_counts.loc[:, position_counts.sum(axis=0).nlargest(top_n).index]
  row_sums = position_counts.sum(axis=1).replace(0, np.nan)
  community = np.sqrt(position_counts.div(row_sums, axis=0).fillna(0))

  environment = pd.read_excel(physicochemistry_path)
  environment.columns = [str(column).strip() for column in environment.columns]
  environment["SampleMM"] = environment["SampleMM"].astype(str).str.strip().replace({"V1.P1": "VI.P1"})
  for column in environment.columns[3:]:
    environment[column] = pd.to_numeric(environment[column], errors="coerce")
  environment_means = environment.groupby("SampleMM").mean(numeric_only=True)

  common = [position for position in position_counts.index if position in environment_means.index]
  community = community.loc[common]
  environment_means = environment_means.loc[common]
  available = [
    column for column in PREFERRED_PREDICTORS
    if column in environment_means.columns and environment_means[column].notna().sum() == len(common)
  ]
  predictors = environment_means[available].copy()
  predictors = predictors.loc[:, predictors.std() > 1e-10]

  selected: list[str] = []
  for column in predictors.columns:
    if not selected or all(abs(predictors[column].corr(predictors[kept])) < correlation_threshold for kept in selected):
      selected.append(column)
    if len(selected) >= maximum_predictors:
      break
  predictors = predictors[selected]
  standardized = (predictors - predictors.mean()) / predictors.std(ddof=0).replace(0, 1)

  design = np.column_stack([np.ones(len(standardized)), standardized.to_numpy()])
  hat = design @ np.linalg.pinv(design.T @ design) @ design.T
  centered = community.to_numpy() - community.to_numpy().mean(axis=0, keepdims=True)
  fitted = hat @ centered
  u, singular_values, vt = np.linalg.svd(fitted, full_matrices=False)
  site = u[:, :2] * singular_values[:2]
  eigenvalues = singular_values ** 2
  axis_percent = 100 * eigenvalues[:2] / max(eigenvalues.sum(), 1e-12)
  vectors = np.array([
    [np.corrcoef(standardized[column], site[:, axis])[0, 1] for axis in range(2)]
    for column in standardized.columns
  ])

  fitted_ss = np.sum(fitted ** 2)
  total_ss = np.sum(centered ** 2)
  constrained_r2 = fitted_ss / total_ss if total_ss else np.nan
  p = len(standardized.columns)
  n = len(standardized)
  df1 = max(p, 1)
  df2 = max(n - p - 1, 1)
  residual_ss = max(total_ss - fitted_ss, 1e-12)
  pseudo_f = (fitted_ss / df1) / (residual_ss / df2)

  generator = np.random.default_rng(random_seed)
  permuted_f: list[float] = []
  for _ in range(permutations):
    permuted = centered[generator.permutation(n), :]
    permuted_fitted = hat @ permuted
    permuted_fitted_ss = np.sum(permuted_fitted ** 2)
    permuted_residual_ss = max(np.sum(permuted ** 2) - permuted_fitted_ss, 1e-12)
    permuted_f.append((permuted_fitted_ss / df1) / (permuted_residual_ss / df2))
  permutation_p = (1 + sum(value >= pseudo_f for value in permuted_f)) / (1 + len(permuted_f))

  scores = pd.DataFrame(site, columns=["RDA1", "RDA2"], index=common)
  scores["Lake"] = [position.split(".")[0] for position in common]
  vector_table = pd.DataFrame(vectors, index=standardized.columns, columns=["RDA1", "RDA2"])
  return {
    "scores": scores,
    "vectors": vector_table,
    "axis_percent": axis_percent,
    "constrained_R2": float(constrained_r2),
    "pseudo_F": float(pseudo_f),
    "permutation_P": float(permutation_p),
    "predictors": selected,
    "n_positions": n,
    "environment_means": environment_means,
  }
