#!/usr/bin/env python3
"""Reproduce the article RDA from compact derived source matrices."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "final_publication_derived"
PREFERRED = ["Fe2O3", "SiO2", "Al2O3", "TOT/C", "TOT/S", "LOI", "V", "Cu", "Pb", "Zr", "Ce"]


def main() -> None:
  community = pd.read_csv(DERIVED / "RDA_hellinger_top80.csv", index_col=0)
  environment = pd.read_csv(
    DERIVED / "fiqui2_physicochemical_sample_means.csv", index_col="SampleMM"
  )
  common = [index for index in community.index if index in environment.index]
  community = community.loc[common]
  environment = environment.loc[common]

  available = [
    column for column in PREFERRED
    if column in environment.columns and environment[column].notna().sum() == len(common)
  ]
  predictors = environment[available].copy()
  predictors = predictors.loc[:, predictors.std() > 1e-10]
  selected: list[str] = []
  for column in predictors.columns:
    if not selected or all(abs(predictors[column].corr(predictors[kept])) < 0.92 for kept in selected):
      selected.append(column)
    if len(selected) >= 6:
      break
  predictors = predictors[selected]
  standardized = (predictors - predictors.mean()) / predictors.std(ddof=0).replace(0, 1)

  design = np.column_stack([np.ones(len(standardized)), standardized.to_numpy()])
  hat = design @ np.linalg.pinv(design.T @ design) @ design.T
  centered = community.to_numpy() - community.to_numpy().mean(axis=0, keepdims=True)
  fitted = hat @ centered
  u, singular_values, _ = np.linalg.svd(fitted, full_matrices=False)
  site = u[:, :2] * singular_values[:2]
  vectors = np.array([
    [np.corrcoef(standardized[column], site[:, axis])[0, 1] for axis in range(2)]
    for column in standardized.columns
  ])

  fitted_ss = np.sum(fitted ** 2)
  total_ss = np.sum(centered ** 2)
  constrained_r2 = fitted_ss / total_ss
  p = len(selected)
  n = len(standardized)
  df1 = max(p, 1)
  df2 = max(n - p - 1, 1)
  residual_ss = max(total_ss - fitted_ss, 1e-12)
  pseudo_f = (fitted_ss / df1) / (residual_ss / df2)

  generator = np.random.default_rng(42)
  permutation_statistics: list[float] = []
  for _ in range(999):
    permuted = centered[generator.permutation(n), :]
    permuted_fitted = hat @ permuted
    permuted_fit_ss = np.sum(permuted_fitted ** 2)
    permuted_residual_ss = max(np.sum(permuted ** 2) - permuted_fit_ss, 1e-12)
    permutation_statistics.append(
      (permuted_fit_ss / df1) / (permuted_residual_ss / df2)
    )
  permutation_p = (
    1 + sum(value >= pseudo_f for value in permutation_statistics)
  ) / (1 + len(permutation_statistics))

  scores = pd.DataFrame(site, columns=["RDA1", "RDA2"], index=common)
  scores["Lake"] = [position.split(".")[0] for position in common]
  vector_table = pd.DataFrame(
    vectors, columns=["RDA1", "RDA2"], index=standardized.columns
  )
  scores.to_csv(DERIVED / "RDA_site_scores_reproduced.csv")
  vector_table.to_csv(DERIVED / "RDA_environment_vectors_reproduced.csv")
  result = {
    "n_positions": n,
    "constrained_R2": float(constrained_r2),
    "pseudo_F": float(pseudo_f),
    "permutation_P": float(permutation_p),
    "predictors": selected,
  }
  print(json.dumps(result, indent=2))


if __name__ == "__main__":
  main()
