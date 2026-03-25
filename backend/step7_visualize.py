"""
Step 7: Visualisation plots.

Produces three PNG files in results/:

1. training_curves.png
   - 2-subplot figure (train/val loss  |  train/val accuracy)
   - One line per phase (phases 1, 2, 3) on a continuous x-axis
   - Vertical dashed lines mark phase boundaries

2. class_distribution.png
   - Horizontal bar chart of per-class image counts in dataset/unified/train/
   - Two stacked bars: TIP images vs. WaDaBa images

3. deformation_accuracy.png
   - Bar chart of WaDaBa test accuracy per deformation level (d0–d3)
   - Data read from results/deformation_results.json  (produced by step 5)

Run: python step7_visualize.py
"""

import json
import os
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
LOG_DIR    = BASE_DIR / "logs"
RESULTS    = BASE_DIR / "results"
UNIFIED_TRAIN = BASE_DIR / "dataset" / "unified" / "train"
DEFORM_JSON   = RESULTS / "deformation_results.json"
RESULTS.mkdir(exist_ok=True)

CLASS_NAMES = sorted(["HDPE", "LDPE", "OTHER", "PET", "PP", "PS"])
PHASE_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c"]   # blue, orange, green


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Training curves
# ═══════════════════════════════════════════════════════════════════════════════
def plot_training_curves() -> None:
    out = RESULTS / "training_curves.png"

    phases: list[pd.DataFrame] = []
    for p in [1, 2, 3]:
        log_path = LOG_DIR / f"phase{p}_log.csv"
        if not log_path.exists():
            print(f"  [WARN] {log_path} not found — training_curves.png may be incomplete")
            phases.append(pd.DataFrame())
        else:
            phases.append(pd.read_csv(log_path))

    if all(df.empty for df in phases):
        print("  [WARN] No phase logs found — skipping training_curves.png")
        return

    fig, (ax_loss, ax_acc) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Training Curves", fontsize=14, fontweight="bold")

    global_offset = 0
    phase_boundaries: list[int] = []

    for p_idx, (df, color) in enumerate(zip(phases, PHASE_COLORS), start=1):
        if df.empty:
            continue

        x = np.arange(global_offset + 1, global_offset + len(df) + 1)

        ax_loss.plot(x, df["train_loss"], color=color, linestyle="-",
                     label=f"Phase {p_idx} train")
        ax_loss.plot(x, df["val_loss"],   color=color, linestyle="--",
                     label=f"Phase {p_idx} val")

        ax_acc.plot(x, df["train_acc"], color=color, linestyle="-",
                    label=f"Phase {p_idx} train")
        ax_acc.plot(x, df["val_acc"],   color=color, linestyle="--",
                    label=f"Phase {p_idx} val")

        global_offset += len(df)
        phase_boundaries.append(global_offset)

    # Vertical phase separators (skip the last one)
    for boundary in phase_boundaries[:-1]:
        ax_loss.axvline(x=boundary + 0.5, color="gray", linestyle=":", alpha=0.6)
        ax_acc.axvline( x=boundary + 0.5, color="gray", linestyle=":", alpha=0.6)

    ax_loss.set_xlabel("Epoch")
    ax_loss.set_ylabel("Loss")
    ax_loss.set_title("Train / Val Loss")
    ax_loss.legend(fontsize=8)
    ax_loss.grid(True, alpha=0.3)

    ax_acc.set_xlabel("Epoch")
    ax_acc.set_ylabel("Accuracy")
    ax_acc.set_title("Train / Val Accuracy")
    ax_acc.legend(fontsize=8)
    ax_acc.grid(True, alpha=0.3)
    ax_acc.set_ylim(0.0, 1.05)

    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Training curves saved → {out}")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Class distribution (stacked TIP / WaDaBa)
# ═══════════════════════════════════════════════════════════════════════════════
def plot_class_distribution() -> None:
    out = RESULTS / "class_distribution.png"

    if not UNIFIED_TRAIN.is_dir():
        print(f"  [WARN] {UNIFIED_TRAIN} not found — skipping class_distribution.png")
        return

    tip_counts    = defaultdict(int)
    wadaba_counts = defaultdict(int)

    for cls in CLASS_NAMES:
        cls_dir = UNIFIED_TRAIN / cls
        if not cls_dir.is_dir():
            continue
        for img_path in cls_dir.glob("*.jpg"):
            if img_path.name.startswith("tip_"):
                tip_counts[cls] += 1
            elif img_path.name.startswith("wadaba_"):
                wadaba_counts[cls] += 1

    tip_vals    = [tip_counts[c]    for c in CLASS_NAMES]
    wadaba_vals = [wadaba_counts[c] for c in CLASS_NAMES]
    totals      = [t + w for t, w in zip(tip_vals, wadaba_vals)]

    y_pos = np.arange(len(CLASS_NAMES))
    fig, ax = plt.subplots(figsize=(10, 6))

    bars_tip    = ax.barh(y_pos, tip_vals, color="#4C72B0", label="TIP")
    bars_wadaba = ax.barh(y_pos, wadaba_vals, left=tip_vals,
                          color="#DD8452", label="WaDaBa")

    # Annotate total counts
    for i, total in enumerate(totals):
        ax.text(total + 5, i, str(total), va="center", fontsize=9)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(CLASS_NAMES)
    ax.set_xlabel("Number of images")
    ax.set_title("Training Set Class Distribution (dataset/unified/train/)")
    ax.legend()
    ax.grid(axis="x", alpha=0.3)

    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Class distribution saved → {out}")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Deformation accuracy
# ═══════════════════════════════════════════════════════════════════════════════
def plot_deformation_accuracy() -> None:
    out = RESULTS / "deformation_accuracy.png"

    if not DEFORM_JSON.exists():
        print(f"  [WARN] {DEFORM_JSON} not found — skipping deformation_accuracy.png")
        return

    with open(DEFORM_JSON) as fh:
        d_acc: dict[str, float] = json.load(fh)

    labels = sorted(d_acc.keys())                       # d0, d1, d2, d3
    values = [d_acc[k] * 100.0 for k in labels]
    level_names = {
        "d0": "d0 — None",
        "d1": "d1 — Low",
        "d2": "d2 — Medium",
        "d3": "d3 — High",
    }
    x_labels = [level_names.get(l, l) for l in labels]

    fig, ax = plt.subplots(figsize=(8, 5))
    colors  = ["#4C72B0", "#55A868", "#C44E52", "#8172B2"]
    bars = ax.bar(x_labels, values, color=colors[: len(labels)], width=0.5)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + 0.5,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=10)

    ax.set_xlabel("Deformation Level")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("WaDaBa Test Accuracy by Deformation Level")
    ax.set_ylim(0, 110)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Deformation accuracy chart saved → {out}")


# ── main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("Step 7 — Visualisation")
    print("=" * 60)

    plot_training_curves()
    plot_class_distribution()
    plot_deformation_accuracy()

    print("\nAll plots saved to", RESULTS)
    print("=" * 60)


if __name__ == "__main__":
    main()
