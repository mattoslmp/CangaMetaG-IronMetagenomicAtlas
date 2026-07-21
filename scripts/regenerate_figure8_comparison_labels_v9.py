#!/usr/bin/env python3
"""Regenerate Figure 8 with exact lake/group comparisons from Supplementary Table 5.

The script preserves the KO values and comparison directions in the source
workbook. Positive log2 fold changes indicate enrichment in the first named
group; negative values indicate enrichment in the second named group.
"""
from __future__ import annotations

import base64
import os
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DERIVED = DATA / "final_publication_derived"
OUT = ROOT / "outputs" / "final_publication_figures"
ARTICLE_MAIN = Path(os.environ.get(
    "CANGAMETAG_ARTICLE_MAIN",
    str(ROOT / "article_outputs" / "02_Main_Figures_title_free"),
))
SOURCE = DATA / "Supplementary_table_5-Differential-abundance-pathways-KOs.xlsx"
COLORS = {"Up": "#1565C0", "Down": "#C62828"}
SHEETS = [
    ("Top-differential-abundance_Dry", "Dry season", "A"),
    ("Top-differential-abundance-Rain", "Rainy season", "B"),
]


def comparison_label(value: object) -> str:
    text = str(value or "").strip()
    return text.replace("vs", " vs ")


def save_all(fig: plt.Figure, folder: Path, stem: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    png = folder / f"{stem}.png"
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    image = Image.open(png).convert("RGB")
    image.save(folder / f"{stem}.pdf", "PDF", resolution=300.0)
    payload = base64.b64encode(png.read_bytes()).decode("ascii")
    (folder / f"{stem}.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{image.width}" '
        f'height="{image.height}" viewBox="0 0 {image.width} {image.height}">'
        f'<image href="data:image/png;base64,{payload}" width="{image.width}" '
        f'height="{image.height}"/></svg>', encoding="utf-8")


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    panels = []
    for sheet, season, panel in SHEETS:
        df = pd.read_excel(SOURCE, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        df["log2FoldChange"] = pd.to_numeric(df["log2FoldChange"], errors="coerce")
        df = df.dropna(subset=["OTU", "log2FoldChange", "Comparasion"]).copy()
        df["Direction"] = np.where(df["log2FoldChange"] >= 0, "Up", "Down")
        df["abs_lfc"] = df["log2FoldChange"].abs()
        df["Label"] = df["OTU"].astype(str).str.replace(r"\s+", " ", regex=True)
        selected = pd.concat([
            df[df["Direction"].eq("Up")].sort_values("abs_lfc", ascending=False)
              .drop_duplicates(subset=["OTU", "Comparasion"]).head(9),
            df[df["Direction"].eq("Down")].sort_values("abs_lfc", ascending=False)
              .drop_duplicates(subset=["OTU", "Comparasion"]).head(9),
        ], ignore_index=True).sort_values("log2FoldChange").reset_index(drop=True)
        selected["Season"] = season
        selected["Panel"] = panel
        panels.append(selected)

    source = pd.concat(panels, ignore_index=True)
    DERIVED.mkdir(parents=True, exist_ok=True)
    source.to_csv(DERIVED / "Figure8_KO_differential_abundance_dry_rainy_source.csv", index=False)

    fig, axes = plt.subplots(2, 1, figsize=(12, 18))
    for ax, (_, season, panel), frame in zip(axes, SHEETS, panels):
        y = np.arange(len(frame))
        bars = ax.barh(y, frame["log2FoldChange"],
                       color=[COLORS[x] for x in frame["Direction"]],
                       edgecolor="white", linewidth=0.8)
        ax.set_yticks(y, [textwrap.shorten(str(x), width=52, placeholder="…")
                          for x in frame["Label"]], fontsize=13)
        ax.axvline(0, color="black", linewidth=1, linestyle="--")
        ax.set_xlabel("log2 fold change", fontsize=15, fontweight="bold")
        ax.set_ylabel("KO / gene marker", fontsize=15, fontweight="bold")
        ax.set_title(f"{panel}  {season} - lake-to-lake differential KO abundance",
                     loc="left", fontsize=18, fontweight="bold")
        maximum = max(1.0, float(frame["abs_lfc"].max()))
        ax.set_xlim(frame["log2FoldChange"].min() - 1.2 * maximum,
                    frame["log2FoldChange"].max() + 1.8 * maximum)
        for bar, (_, row) in zip(bars, frame.iterrows()):
            value = float(bar.get_width())
            xpos = value + 0.08 * maximum if value >= 0 else value - 0.08 * maximum
            ax.text(xpos, bar.get_y() + bar.get_height() / 2,
                    f"{comparison_label(row['Comparasion'])} | {value:.2f}",
                    va="center", ha="left" if value >= 0 else "right",
                    fontsize=12, color="black")
        ax.tick_params(axis="x", labelsize=12)
        ax.grid(axis="x", alpha=0.15)

    fig.legend(handles=[
        Patch(color=COLORS["Up"], label="Positive / enriched in the first lake or group"),
        Patch(color=COLORS["Down"], label="Negative / enriched in the second lake or group"),
    ], loc="upper center", bbox_to_anchor=(0.5, 0.975), ncol=2,
       frameon=False, fontsize=12)
    fig.suptitle(
        "Differential KO/gene abundance across lake-to-lake comparisons in dry and rainy periods",
        fontsize=21, fontweight="bold", y=0.995)
    fig.subplots_adjust(left=0.25, right=0.96, top=0.93, bottom=0.05, hspace=0.22)
    stem = "Figure8_KO_differential_abundance_dry_rainy"
    for folder in (OUT, ARTICLE_MAIN):
        save_all(fig, folder, stem)
    plt.close(fig)
    print(f"Generated {stem} from {SOURCE}")


if __name__ == "__main__":
    main()
