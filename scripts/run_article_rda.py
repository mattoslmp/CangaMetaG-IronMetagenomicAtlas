#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

from src.article_rda import load_cds, run_article_rda

DATA = ROOT / "data"
OUT = DATA / "final_publication_derived"


def main() -> None:
  OUT.mkdir(parents=True, exist_ok=True)
  otu, taxonomy = load_cds(DATA)
  result = run_article_rda(otu, taxonomy, DATA / "fiqui2.xlsx")
  result["scores"].to_csv(OUT / "RDA_site_scores.csv")
  result["vectors"].to_csv(OUT / "RDA_environment_vectors.csv")
  result["environment_means"].reset_index().to_csv(
    OUT / "fiqui2_physicochemical_sample_means.csv", index=False
  )
  summary = {
    "n_positions": result["n_positions"],
    "constrained_R2": result["constrained_R2"],
    "pseudo_F": result["pseudo_F"],
    "permutation_P": result["permutation_P"],
    "predictors": result["predictors"],
  }
  (OUT / "RDA_model_summary.json").write_text(
    json.dumps(summary, indent=2) + "\n", encoding="utf-8"
  )
  print(json.dumps(summary, indent=2))


if __name__ == "__main__":
  main()
