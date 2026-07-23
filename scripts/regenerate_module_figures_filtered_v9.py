#!/usr/bin/env python3
"""Regenerate the canonical KEGG/KEMET module-completeness figures.

Scientific display rule
-----------------------
Only calls classified as ``Complete`` or ``1 block missing`` are drawn. Calls
with more than one missing block, incomplete calls, and absent calls remain
blank. A module row is retained when at least one record has a displayed call.
The complete source matrices are never modified and remain available for audit.

The same filtered matrices generate:
- paginated manuscript panels for Supplementary Figures 37, 38, 40, and 67;
- one integral, zoomable figure per heatmap for the Streamlit application;
- PNG, PDF, and SVG outputs;
- filtered numeric/status tables and an execution manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from PIL import Image

BLUE = "#1565C0"
GREEN = "#2E7D32"
DISPLAY_STATUSES = ("1 block missing", "Complete")


@dataclass(frozen=True)
class FigureConfig:
  figure: int
  source_file: str
  stem: str
  panel_title: str
  x_label: str
  rows_per_panel: int
  cols_per_panel: int | None
  panel_size: tuple[float, float]
  left: float
  right: float
  bottom: float
  top: float
  x_rotation: float
  x_fontsize: float
  y_fontsize: float
  y_wrap: int
  x_wrap: int


CONFIGS = (
  FigureConfig(
    37,
    "MAG_KEGG_module_completeness_STATUS_species_MAGnumber_3state.csv",
    "SupplementaryFigure37_MAG_KEGG_module_completeness_heatmap_species_MAGnumber_KEMET_style_3state",
    "MAG KEGG/KEMET module completeness",
    "Recovered MAGs",
    11,
    None,
    (15.20, 5.695),
    0.340,
    0.990,
    0.600,
    0.850,
    90.0,
    7.2,
    7.5,
    200,
    200,
  ),
  FigureConfig(
    38,
    "KEMET_lagoon_all_metagenomes_module_completeness_STATUS_3state.csv",
    "SupplementaryFigure38_metagenome_KEGG_module_completeness_heatmap",
    "Amazonian lagoon metagenome KEGG/KEMET module completeness",
    "Amazonian lagoon metagenomes",
    22,
    None,
    (11.461, 8.25),
    0.455,
    0.990,
    0.225,
    0.885,
    58.0,
    9.0,
    8.0,
    86,
    24,
  ),
  FigureConfig(
    40,
    "ST8_external_iron_rich_module_completeness_STATUS_3state_from_KO.csv",
    "SupplementaryFigure40_ST8_external_iron_rich_module_completeness_KEMET_style_3state_heatmap",
    "External iron-rich metagenome KEGG/KEMET module completeness",
    "External iron-rich metagenomes",
    21,
    24,
    (14.349, 8.25),
    0.405,
    0.990,
    0.315,
    0.875,
    62.0,
    8.8,
    7.7,
    96,
    21,
  ),
  FigureConfig(
    67,
    "Combined_lagoon_plus_external_iron_rich_module_completeness_STATUS_3state.csv",
    "SupplementaryFigure67_lagoon_plus_external_iron_rich_module_completeness_KEMET_style_3state_heatmap",
    "Amazonian plus external module completeness — modules complete in at least one record",
    "Amazonian and external iron-rich metagenomes",
    26,
    22,
    (15.25, 7.251),
    0.420,
    0.990,
    0.300,
    0.790,
    62.0,
    8.4,
    7.3,
    105,
    20,
  ),
)


def sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for block in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(block)
  return digest.hexdigest()


def clean_label(value: object) -> str:
  text = str(value if value is not None else "").strip()
  if not text or text.casefold() in {"nan", "none", "undefined", "null", "unnamed: 0"}:
    return "Unlabelled KEGG module"
  return re.sub(r"\s+", " ", text.replace(" => ", " → "))


def normalize_status(value: object) -> str:
  text = re.sub(r"\s+", " ", str(value if value is not None else "").strip()).casefold()
  if text == "complete":
    return "Complete"
  if text in {"1 block missing", "one block missing"}:
    return "1 block missing"
  return "Not displayed"


def load_filtered_matrix(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
  source = pd.read_csv(path)
  first = source.columns[0]
  source[first] = source[first].map(clean_label)
  source = source.drop_duplicates(subset=[first], keep="first").set_index(first)
  status = source.map(normalize_status)
  keep = status.isin(DISPLAY_STATUSES).any(axis=1)
  filtered = status.loc[keep].copy()
  codes = filtered.replace({"Not displayed": 0, "1 block missing": 1, "Complete": 2}).astype(int)
  return filtered, codes


def wrap_plain(value: object, width: int) -> str:
  return "\n".join(textwrap.wrap(clean_label(value), width=max(8, width), break_long_words=False, break_on_hyphens=False))


def panel_slices(config: FigureConfig, n_rows: int, n_cols: int):
  row_chunks = [(start, min(start + config.rows_per_panel, n_rows)) for start in range(0, n_rows, config.rows_per_panel)]
  width = config.cols_per_panel or n_cols
  col_chunks = [(start, min(start + width, n_cols)) for start in range(0, n_cols, width)]
  for row_start, row_end in row_chunks:
    for col_start, col_end in col_chunks:
      yield row_start, row_end, col_start, col_end


def title_for(config: FigureConfig, panel_id: str) -> str:
  if config.figure == 67:
    return f"{config.panel_title} — Panel {panel_id}"
  return f"{config.panel_title} — Panel {panel_id}"


def make_panel(
  config: FigureConfig,
  codes: pd.DataFrame,
  row_slice: tuple[int, int],
  col_slice: tuple[int, int],
  panel_id: str,
) -> plt.Figure:
  row_start, row_end = row_slice
  col_start, col_end = col_slice
  subset = codes.iloc[row_start:row_end, col_start:col_end]
  matrix = subset.to_numpy(dtype=float)
  matrix[matrix == 0] = np.nan
  cmap = ListedColormap([BLUE, GREEN])
  cmap.set_bad("white")
  norm = BoundaryNorm([0.5, 1.5, 2.5], cmap.N)

  fig, ax = plt.subplots(figsize=config.panel_size, facecolor="white")
  ax.imshow(matrix, aspect="auto", interpolation="nearest", cmap=cmap, norm=norm)
  xlabels = [wrap_plain(x, config.x_wrap) for x in subset.columns]
  ylabels = [wrap_plain(y, config.y_wrap) for y in subset.index]
  ax.set_xticks(np.arange(len(xlabels)), labels=xlabels, rotation=config.x_rotation, ha="right", rotation_mode="anchor", fontsize=config.x_fontsize)
  ax.set_yticks(np.arange(len(ylabels)), labels=ylabels, fontsize=config.y_fontsize)
  ax.tick_params(axis="both", length=0, pad=2)
  ax.set_xlabel(config.x_label, fontsize=11.5, fontweight="bold", labelpad=8)
  ax.set_ylabel("KEGG/KEMET module and metabolic pathway", fontsize=10.5, fontweight="bold", labelpad=6)
  title_size = 11.0 if config.figure == 67 else 12.0
  ax.set_title(title_for(config, panel_id), fontsize=title_size, fontweight="bold", loc="left", pad=9, wrap=True)
  ax.legend(
    handles=(Patch(facecolor=GREEN, label="Complete"), Patch(facecolor=BLUE, label="1 block missing")),
    loc="upper left",
    bbox_to_anchor=(0.0, 1.015),
    ncol=2,
    frameon=False,
    fontsize=8.8,
    borderaxespad=0.0,
    handlelength=1.2,
    columnspacing=1.2,
  )
  for spine in ax.spines.values():
    spine.set_visible(False)
  fig.text(
    config.left,
    0.012,
    "Only Complete and 1 block missing calls are shown; calls with more than one missing block are blank.",
    fontsize=7.8,
  )
  fig.subplots_adjust(left=config.left, right=config.right, bottom=config.bottom, top=config.top)
  return fig


def save_figure(fig: plt.Figure, stem: Path, png_dpi: int) -> dict[str, str]:
  """Render once to PNG, then derive PDF and SVG deterministically.

  This avoids re-laying out dense text three times. The SVG keeps the exact PNG
  pixels as an embedded, standards-compliant image so the PNG/PDF/SVG copies
  are guaranteed to derive from the same rendering.
  """
  import base64

  stem.parent.mkdir(parents=True, exist_ok=True)
  png = stem.with_suffix(".png")
  pdf = stem.with_suffix(".pdf")
  svg = stem.with_suffix(".svg")
  fig.savefig(png, dpi=png_dpi, facecolor="white", pil_kwargs={"compress_level": 1})
  with Image.open(png) as image:
    rgb = image.convert("RGB")
    rgb.save(pdf, "PDF", resolution=float(png_dpi))
    width, height = rgb.size
  payload = base64.b64encode(png.read_bytes()).decode("ascii")
  svg.write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}"><image href="data:image/png;base64,{payload}" '
    f'width="{width}" height="{height}"/></svg>',
    encoding="utf-8",
  )
  return {str(path.suffix).lstrip("."): sha256(path) for path in (png, pdf, svg)}


def make_full_integral(config: FigureConfig, codes: pd.DataFrame) -> plt.Figure:
  n_rows, n_cols = codes.shape
  matrix = codes.to_numpy(dtype=float)
  matrix[matrix == 0] = np.nan
  cmap = ListedColormap([BLUE, GREEN])
  cmap.set_bad("white")
  norm = BoundaryNorm([0.5, 1.5, 2.5], cmap.N)

  fig_w = max(18.0, min(38.0, 8.0 + 0.34 * n_cols))
  fig_h = max(16.0, min(70.0, 5.0 + 0.20 * n_rows))
  fig, ax = plt.subplots(figsize=(fig_w, fig_h), facecolor="white")
  ax.imshow(matrix, aspect="auto", interpolation="nearest", cmap=cmap, norm=norm)
  ax.set_xticks(np.arange(n_cols), labels=[wrap_plain(x, 24) for x in codes.columns], rotation=65, ha="right", rotation_mode="anchor", fontsize=9.8)
  ax.set_yticks(np.arange(n_rows), labels=[wrap_plain(y, 70) for y in codes.index], fontsize=9.3)
  ax.tick_params(axis="both", length=0, pad=2)
  ax.set_xlabel(config.x_label, fontsize=15, fontweight="bold", labelpad=14)
  ax.set_ylabel("KEGG/KEMET module and metabolic pathway", fontsize=14, fontweight="bold", labelpad=8)
  if config.figure == 67:
    total_panels = sum(1 for _ in panel_slices(config, n_rows, n_cols))
    title = f"{config.panel_title} — Panels P001–P{total_panels:03d} combined"
  else:
    title = f"{config.panel_title} — complete integral application view"
  ax.set_title(title, fontsize=18, fontweight="bold", loc="left", pad=13, wrap=True)
  ax.legend(
    handles=(Patch(facecolor=GREEN, label="Complete"), Patch(facecolor=BLUE, label="1 block missing")),
    title="Displayed KEMET status",
    loc="upper left",
    bbox_to_anchor=(1.002, 1.0),
    frameon=False,
    fontsize=11,
    title_fontsize=12,
  )
  for spine in ax.spines.values():
    spine.set_visible(False)
  left = min(0.44, max(0.18, 5.2 / fig_w))
  bottom = min(0.30, max(0.10, 2.6 / fig_h))
  fig.text(left, 0.008, "Only Complete and 1 block missing calls are shown; all other source calls are blank.", fontsize=10)
  fig.subplots_adjust(left=left, right=0.91, bottom=bottom, top=0.965)
  return fig


def run_config(
  config: FigureConfig,
  root: Path,
  article_root: Path | None,
  png_dpi: int,
  panel_start: int = 1,
  panel_end: int | None = None,
  skip_full: bool = False,
  full_only: bool = False,
) -> dict:
  data_path = root / "data" / "final_kegg_st8_update" / config.source_file
  filtered_status, codes = load_filtered_matrix(data_path)
  final_dir = root / "outputs" / "final_publication_figures"
  app_dir = root / "outputs" / "app_supplementary_figures"
  article_dir = article_root / "03_Supplementary_Figures" if article_root else None
  derived_dir = root / "data" / "final_publication_derived"
  derived_dir.mkdir(parents=True, exist_ok=True)
  filtered_status.to_csv(derived_dir / f"{config.stem}_filtered_status.csv")
  codes.to_csv(derived_dir / f"{config.stem}_filtered_codes.csv")

  panels = list(panel_slices(config, *codes.shape))
  requested_end = panel_end or len(panels)
  requested_end = min(requested_end, len(panels))
  panel_records = []
  if not full_only:
    for panel_number, (row_start, row_end, col_start, col_end) in enumerate(panels, start=1):
      if panel_number < panel_start or panel_number > requested_end:
        continue
      panel_id = f"P{panel_number:03d}"
      fig = make_panel(config, codes, (row_start, row_end), (col_start, col_end), panel_id)
      stem = final_dir / f"{config.stem}_{panel_id}"
      hashes = save_figure(fig, stem, png_dpi)
      if article_dir:
        article_dir.mkdir(parents=True, exist_ok=True)
        for suffix in (".png", ".pdf", ".svg"):
          target = article_dir / f"{config.stem}_{panel_id}{suffix}"
          target.write_bytes(stem.with_suffix(suffix).read_bytes())
      panel_records.append({
        "panel": panel_id,
        "rows": [row_start + 1, row_end],
        "columns": [col_start + 1, col_end],
        "hashes": hashes,
      })
      plt.close(fig)

  panel_pdf_paths = [final_dir / f"{config.stem}_P{i:03d}.pdf" for i in range(1, len(panels) + 1)]
  multipage_pdf = final_dir / f"{config.stem}.pdf"
  if all(path.exists() for path in panel_pdf_paths):
    try:
      from pypdf import PdfReader, PdfWriter
      writer = PdfWriter()
      for panel_pdf in panel_pdf_paths:
        reader = PdfReader(str(panel_pdf))
        for page in reader.pages:
          writer.add_page(page)
      with multipage_pdf.open("wb") as handle:
        writer.write(handle)
    except Exception:
      import subprocess
      subprocess.run(["pdfunite", *map(str, panel_pdf_paths), str(multipage_pdf)], check=True)
  pdf_pages_path = str(multipage_pdf)

  # Backward-compatible preview in the publication directory: exact first panel.
  for suffix in (".png", ".svg"):
    source = final_dir / f"{config.stem}_P001{suffix}"
    if source.exists():
      preview = final_dir / f"{config.stem}{suffix}"
      preview.write_bytes(source.read_bytes())

  full_hashes = {}
  if not skip_full:
    full_fig = make_full_integral(config, codes)
    full_hashes = save_figure(full_fig, app_dir / config.stem, 100)
    plt.close(full_fig)

  return {
    "figure": f"S{config.figure}",
    "source": str(data_path.relative_to(root)),
    "source_sha256": sha256(data_path),
    "shape_source": [int(pd.read_csv(data_path).shape[0]), int(pd.read_csv(data_path).shape[1] - 1)],
    "shape_displayed": [int(codes.shape[0]), int(codes.shape[1])],
    "filter": "display Complete and 1 block missing; blank all other calls; retain rows with at least one displayed call",
    "panel_count": len(panels),
    "multipage_pdf": pdf_pages_path,
    "multipage_pdf_sha256": sha256(multipage_pdf) if multipage_pdf.exists() else None,
    "integral_app_output": str((app_dir / config.stem).relative_to(root)),
    "integral_hashes": full_hashes,
    "panels": panel_records,
  }


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser()
  parser.add_argument("--base-dir", type=Path, default=Path(__file__).resolve().parents[1])
  parser.add_argument("--article-root", type=Path)
  parser.add_argument("--png-dpi", type=int, default=220)
  parser.add_argument("--only", choices=["37", "38", "40", "67"], action="append")
  parser.add_argument("--panel-start", type=int, default=1)
  parser.add_argument("--panel-end", type=int)
  parser.add_argument("--skip-full", action="store_true")
  parser.add_argument("--full-only", action="store_true")
  return parser.parse_args()


def main() -> int:
  args = parse_args()
  root = args.base_dir.resolve()
  article_root = args.article_root.resolve() if args.article_root else None
  selected = {int(x) for x in args.only} if args.only else {c.figure for c in CONFIGS}
  records = []
  for config in CONFIGS:
    if config.figure not in selected:
      continue
    print(f"Generating S{config.figure} from {config.source_file}", flush=True)
    records.append(run_config(
      config,
      root,
      article_root,
      args.png_dpi,
      panel_start=args.panel_start,
      panel_end=args.panel_end,
      skip_full=args.skip_full,
      full_only=args.full_only,
    ))
  validation_dir = root / "validation"
  validation_dir.mkdir(parents=True, exist_ok=True)
  report = {
    "script": str(Path(__file__).relative_to(root)),
    "executed_utc": datetime.now(timezone.utc).isoformat(),
    "python": sys.version,
    "matplotlib": matplotlib.__version__,
    "pandas": pd.__version__,
    "numpy": np.__version__,
    "display_statuses": list(DISPLAY_STATUSES),
    "records": records,
  }
  path = validation_dir / "module_figures_filtered_v9_execution.json"
  path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
  print(path)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
