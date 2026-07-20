#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = ROOT / "validation" / "RDA_ARTICLE_REFERENCE.json"
REPORT_PATH = ROOT / "validation" / "RDA_CONSISTENCY_REPORT.json"
SCRIPT_PATH = ROOT / "scripts" / "consolidate_final_publication.py"


def sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for block in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(block)
  return digest.hexdigest()


def close_enough(value: float, expected: float, tolerance: float = 1e-12) -> bool:
  return math.isfinite(value) and abs(value - expected) <= tolerance


def load_article_module():
  specification = importlib.util.spec_from_file_location("article_rda", SCRIPT_PATH)
  if specification is None or specification.loader is None:
    raise RuntimeError(f"Could not import {SCRIPT_PATH}")
  module = importlib.util.module_from_spec(specification)
  specification.loader.exec_module(module)
  return module


def main() -> int:
  reference = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
  expected = reference["model"]
  issues: list[str] = []

  module = load_article_module()
  otu, taxonomy = module.load_cds()
  result = module.rda_analysis(otu, taxonomy)

  observed = {
    "n_positions": int(result["n"]),
    "constrained_R2": float(result["r2"]),
    "pseudo_F": float(result["F"]),
    "permutation_P": float(result["p"]),
    "predictors": list(result["variables"]),
  }

  if observed["n_positions"] != expected["n_positions"]:
    issues.append(
      f"n_positions={observed['n_positions']}; expected {expected['n_positions']}"
    )
  if observed["predictors"] != expected["predictors"]:
    issues.append(
      "predictors=" + ", ".join(observed["predictors"])
      + "; expected " + ", ".join(expected["predictors"])
    )
  for field in ("constrained_R2", "pseudo_F", "permutation_P"):
    if not close_enough(observed[field], float(expected[field])):
      issues.append(
        f"{field}={observed[field]!r}; expected {expected[field]!r}"
      )

  hash_results: dict[str, dict[str, object]] = {}
  for relative, expected_hash in reference["sha256"].items():
    path = ROOT / relative
    if not path.is_file():
      issues.append(f"missing canonical file: {relative}")
      hash_results[relative] = {
        "exists": False,
        "expected": expected_hash,
        "observed": None,
        "matches": False,
      }
      continue
    observed_hash = sha256(path)
    matches = observed_hash == expected_hash
    hash_results[relative] = {
      "exists": True,
      "expected": expected_hash,
      "observed": observed_hash,
      "matches": matches,
    }
    if not matches:
      issues.append(f"SHA-256 mismatch: {relative}")

  report = {
    "status": "PASS" if not issues else "FAIL",
    "article_rda_reference": expected,
    "observed": observed,
    "hashes": hash_results,
    "issues": issues,
  }
  REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
  REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
  print(json.dumps(report, indent=2))
  return 1 if issues else 0


if __name__ == "__main__":
  raise SystemExit(main())
