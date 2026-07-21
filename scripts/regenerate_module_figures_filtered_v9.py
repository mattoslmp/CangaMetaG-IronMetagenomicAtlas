#!/usr/bin/env python3
"""Regenerate KEGG/KEMET module figures using the final display filter.

Display rule
------------
A module call is drawn only when its status is either ``Complete`` or
``1 block missing``. Calls with two or more missing blocks are not shown. A
module row is retained only if at least one sample meets the display rule.

This implements the manuscript-requested filter for MAGs, lagoon metagenomes,
external iron-rich metagenomes, and the combined matrix.
"""
from __future__ import annotations

import base64
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "final_kegg_st8_update"
OUT = ROOT / "outputs" / "final_publication_figures"
APP_SUPP = ROOT / "outputs" / "app_supplementary_figures"
ARTICLE_SUPP = Path(os.environ.get(
    "CANGAMETAG_ARTICLE_SUPP",
    str(ROOT / "article_outputs" / "03_Supplementary_Figures"),
))
BLUE, GREEN = "#1565C0", "#2E7D32"

CONFIG = [
    ("MAG_KEGG_module_completeness_STATUS_species_MAGnumber_3state.csv",
     "SupplementaryFigure37_MAG_KEGG_module_completeness_heatmap_species_MAGnumber_KEMET_style_3state",
     "MAG KEGG module completeness", "MAGs", (18, 18)),
    ("KEMET_lagoon_all_metagenomes_module_completeness_STATUS_3state.csv",
     "SupplementaryFigure38_metagenome_KEGG_module_completeness_heatmap",
     "Lagoon metagenome KEGG module completeness", "Lagoon metagenomes", (18, 21)),
    ("ST8_external_iron_rich_module_completeness_STATUS_3state_from_KO.csv",
     "SupplementaryFigure40_ST8_external_iron_rich_module_completeness_KEMET_style_3state_heatmap",
     "External iron-rich metagenome KEGG module completeness",
     "External iron-rich metagenomes", (22, 24)),
    ("Combined_lagoon_plus_external_iron_rich_module_completeness_STATUS_3state.csv",
     "SupplementaryFigure67_lagoon_plus_external_iron_rich_module_completeness_KEMET_style_3state_heatmap",
     "Combined lagoon and external iron-rich KEGG module completeness",
     "Lagoon + external iron-rich metagenomes", (25, 26)),
]


def clean_label(value: object) -> str:
    text = str(value if value is not None else "").strip()
    if not text or text.casefold() in {"nan", "none", "undefined", "null"}:
        return "Unlabelled KEGG module"
    return re.sub(r"\s+", " ", text.replace(" => ", " → "))


def status_code(value: object) -> int:
    text = str(value if value is not None else "").strip().casefold()
    if text == "complete":
        return 2
    if text in {"1 block missing", "one block missing"}:
        return 1
    return 0


def save_all_formats(fig: plt.Figure, stem: Path, dpi: int = 120) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    png = stem.with_suffix(".png")
    fig.savefig(png, dpi=dpi, bbox_inches="tight", facecolor="white")
    image = Image.open(png).convert("RGB")
    image.save(stem.with_suffix(".pdf"), "PDF", resolution=float(dpi))
    payload = base64.b64encode(png.read_bytes()).decode("ascii")
    stem.with_suffix(".svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{image.width}" '
        f'height="{image.height}" viewBox="0 0 {image.width} {image.height}">'
        f'<image href="data:image/png;base64,{payload}" width="{image.width}" '
        f'height="{image.height}"/></svg>',
        encoding="utf-8",
    )


def filtered_codes(filename: str) -> pd.DataFrame:
    df = pd.read_csv(DATA / filename)
    first = df.columns[0]
    df[first] = df[first].map(clean_label)
    df = df.drop_duplicates(subset=[first]).set_index(first).fillna("Incomplete")
    codes = df.map(status_code)
    codes = codes.loc[(codes >= 1).any(axis=1)]
    signal = (2 * codes.eq(2).sum(axis=1) + codes.eq(1).sum(axis=1)).sort_values(ascending=False)
    return codes.loc[signal.index]


def heatmap(filename: str, stem_name: str, title: str, xlabel: str,
            figsize: tuple[float, float]) -> None:
    codes = filtered_codes(filename)
    matrix = codes.to_numpy(dtype=float)
    matrix[matrix < 1] = np.nan
    cmap = ListedColormap([BLUE, GREEN])
    cmap.set_bad("white")
    norm = BoundaryNorm([0.5, 1.5, 2.5], cmap.N)

    fig_w = max(18.0, min(40.0, 10.0 + 0.32 * codes.shape[1]))
    fig_h = max(16.0, min(82.0, 5.0 + 0.24 * codes.shape[0]))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), facecolor="white")
    ax.imshow(matrix, aspect="auto", interpolation="nearest", cmap=cmap, norm=norm)
    ax.set_xticks(np.arange(codes.shape[1]), labels=[str(c) for c in codes.columns],
                  rotation=65, ha="right", fontsize=11.0)
    ax.set_yticks(np.arange(codes.shape[0]), labels=[clean_label(x) for x in codes.index],
                  fontsize=10.5)
    ax.tick_params(axis="both", length=0, pad=1)
    ax.set_xlabel(xlabel, fontsize=15, fontweight="bold", labelpad=16)
    ax.set_ylabel("KEGG/KEMET module and metabolic pathway", fontsize=13,
                  fontweight="bold", labelpad=6)
    ax.set_title(title, fontsize=20, fontweight="bold", loc="left", pad=12)
    ax.legend(
        handles=[Patch(facecolor=GREEN, label="Complete"),
                 Patch(facecolor=BLUE, label="1 block missing")],
        title="Displayed KEMET status", loc="upper left",
        bbox_to_anchor=(1.0, 1.0), frameon=False, fontsize=12,
        title_fontsize=13,
    )
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.text(
        0.01, 0.008,
        f"Only Complete or 1 block missing calls are shown. {len(codes):,} module rows "
        "have at least one displayed call; calls with more than one missing block are blank.",
        fontsize=11.0,
    )
    fig.tight_layout(rect=[0, 0.025, 0.92, 0.98])
    for folder in (OUT, APP_SUPP, ARTICLE_SUPP):
        save_all_formats(fig, folder / stem_name)
    plt.close(fig)
    target = ROOT / "data" / "final_publication_derived"
    target.mkdir(parents=True, exist_ok=True)
    codes.to_csv(target / f"{stem_name}_filtered_codes.csv")
    print(stem_name, codes.shape)


def summary_barplot() -> None:
    codes = filtered_codes("ST8_external_iron_rich_module_completeness_STATUS_3state_from_KO.csv")
    counts = pd.DataFrame({
        "Complete": codes.eq(2).sum(axis=0),
        "1 block missing": codes.eq(1).sum(axis=0),
    })
    fig, ax = plt.subplots(figsize=(max(14, 0.34 * len(counts) + 7), 8.5))
    bottom = np.zeros(len(counts))
    for status, color in (("Complete", GREEN), ("1 block missing", BLUE)):
        values = counts[status].to_numpy(float)
        ax.bar(np.arange(len(counts)), values, bottom=bottom, color=color,
               edgecolor="white", linewidth=0.4, label=status)
        bottom += values
    ax.set_xticks(np.arange(len(counts)), labels=[str(x) for x in counts.index],
                  rotation=65, ha="right", fontsize=10.2)
    ax.set_ylabel("Number of displayed KEGG/KEMET modules", fontsize=15, fontweight="bold")
    ax.set_xlabel("External iron-rich metagenome", fontsize=15, fontweight="bold")
    ax.set_title("External iron-rich metagenome module-status summary",
                 fontsize=20, fontweight="bold")
    ax.legend(frameon=False, fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    stem = "SupplementaryFigure41_ST8_external_iron_rich_module_status_summary_3state_barplot"
    for folder in (OUT, APP_SUPP, ARTICLE_SUPP):
        save_all_formats(fig, folder / stem, dpi=180)
    plt.close(fig)
    target = ROOT / "data" / "final_publication_derived"
    target.mkdir(parents=True, exist_ok=True)
    counts.to_csv(target / f"{stem}_source.csv")


def main() -> None:
    for cfg in CONFIG:
        heatmap(*cfg)
    summary_barplot()


if __name__ == "__main__":
    main()
