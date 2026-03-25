"""
Step 5: Evaluate the trained model on the test split.

Loads checkpoints/phase3_best.pth and runs inference on dataset/unified/test/.

Outputs (all in results/):
  confusion_matrix.png          — colour-coded normalised confusion matrix
  evaluation_report.txt         — sklearn classification report + WaDaBa group analysis
  deformation_results.json      — {d0: acc, d1: acc, d2: acc, d3: acc}
  dirtiness_results.json        — {e0: acc, e1: acc, e2: acc, e3: acc}

Hardware: GPU required.

Run: python step5_evaluate.py
"""

import json
import os
from pathlib import Path
from collections import defaultdict

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from torchvision.datasets import ImageFolder
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

try:
    from torchvision.models import efficientnet_b3, EfficientNet_B3_Weights
    def build_backbone() -> nn.Module:
        return efficientnet_b3(weights=EfficientNet_B3_Weights.DEFAULT)
except ImportError:
    import torchvision
    def build_backbone() -> nn.Module:          # type: ignore[misc]
        return torchvision.models.efficientnet_b3(pretrained=False)

# ── GPU guard ─────────────────────────────────────────────────────────────────
assert torch.cuda.is_available(), "CUDA GPU is required for evaluation."
DEVICE = torch.device("cuda")

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
CKPT_PATH  = BASE_DIR / "checkpoints" / "phase3_best.pth"
TEST_DIR   = BASE_DIR / "dataset" / "unified" / "test"
META_CSV   = BASE_DIR / "wadaba_metadata.csv"
RESULTS    = BASE_DIR / "results"
RESULTS.mkdir(exist_ok=True)

NUM_CLASSES = 6
IMG_SIZE    = 300
NUM_WORKERS = 4
BATCH_SIZE  = 32

CLASS_NAMES = sorted(["HDPE", "LDPE", "OTHER", "PET", "PP", "PS"])

VAL_TF = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


# ── model ─────────────────────────────────────────────────────────────────────
def load_model() -> nn.Module:
    model = build_backbone()
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(1536, 512),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.2),
        nn.Linear(512, NUM_CLASSES),
    )
    state = torch.load(CKPT_PATH, map_location=DEVICE)
    model.load_state_dict(state)
    model.to(DEVICE).eval()
    return model


# ── dataset that also returns image paths ─────────────────────────────────────
class ImageFolderWithPaths(ImageFolder):
    """Extends ImageFolder to return (image, label, path) tuples."""
    def __getitem__(self, index):
        img, label = super().__getitem__(index)
        path = self.samples[index][0]
        return img, label, path


# ── inference ─────────────────────────────────────────────────────────────────
def run_inference(model: nn.Module) -> tuple[list[int], list[int], list[str]]:
    """Returns (all_preds, all_labels, all_paths)."""
    ds = ImageFolderWithPaths(str(TEST_DIR), transform=VAL_TF)
    loader = DataLoader(
        ds, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=NUM_WORKERS, pin_memory=True,
    )

    all_preds:  list[int] = []
    all_labels: list[int] = []
    all_paths:  list[str] = []

    with torch.no_grad():
        for imgs, labels, paths in loader:
            imgs = imgs.to(DEVICE, non_blocking=True)
            logits = model(imgs)
            preds  = logits.argmax(1).cpu().tolist()
            all_preds.extend(preds)
            all_labels.extend(labels.tolist())
            all_paths.extend(paths)

    return all_preds, all_labels, all_paths


# ── confusion matrix plot ─────────────────────────────────────────────────────
def plot_confusion_matrix(y_true: list[int], y_pred: list[int]) -> None:
    cm = confusion_matrix(y_true, y_pred)
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)

    fig, ax = plt.subplots(figsize=(8, 6))
    img = ax.imshow(cm_norm, interpolation="nearest", cmap="Blues",
                    vmin=0.0, vmax=1.0)
    plt.colorbar(img, ax=ax)

    ax.set_xticks(range(NUM_CLASSES))
    ax.set_yticks(range(NUM_CLASSES))
    ax.set_xticklabels(CLASS_NAMES, rotation=45, ha="right")
    ax.set_yticklabels(CLASS_NAMES)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Normalised Confusion Matrix")

    thresh = 0.5
    for i in range(NUM_CLASSES):
        for j in range(NUM_CLASSES):
            ax.text(j, i, f"{cm_norm[i, j]:.2f}",
                    ha="center", va="center",
                    color="white" if cm_norm[i, j] > thresh else "black",
                    fontsize=8)

    fig.tight_layout()
    out = RESULTS / "confusion_matrix.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Confusion matrix saved → {out}")


# ── WaDaBa deformation / dirtiness analysis ──────────────────────────────────
def wadaba_group_analysis(
    all_preds:  list[int],
    all_labels: list[int],
    all_paths:  list[str],
) -> tuple[dict[str, float], dict[str, float]]:
    """Return per-deformation and per-dirtiness accuracy dicts."""
    if not META_CSV.exists():
        print(f"[WARN] {META_CSV} not found — skipping WaDaBa group analysis")
        return {}, {}

    meta_df = pd.read_csv(META_CSV)
    # Build lookup: filename → (deformation_level, dirtiness_level)
    meta_lookup: dict[str, tuple[int, int]] = {
        row["filename"]: (int(row["deformation_level"]), int(row["dirtiness_level"]))
        for _, row in meta_df.iterrows()
    }

    deform_correct:  dict[int, int] = defaultdict(int)
    deform_total:    dict[int, int] = defaultdict(int)
    dirty_correct:   dict[int, int] = defaultdict(int)
    dirty_total:     dict[int, int] = defaultdict(int)

    for pred, label, path in zip(all_preds, all_labels, all_paths):
        fname = os.path.basename(path)
        if fname not in meta_lookup:
            continue
        d_level, e_level = meta_lookup[fname]
        correct = int(pred == label)

        deform_correct[d_level] += correct
        deform_total[d_level]   += 1
        dirty_correct[e_level]  += correct
        dirty_total[e_level]    += 1

    def _to_acc(c_map, t_map):
        return {
            f"d{lvl}": c_map[lvl] / t_map[lvl]
            for lvl in sorted(t_map) if t_map[lvl] > 0
        }

    def _to_acc_e(c_map, t_map):
        return {
            f"e{lvl}": c_map[lvl] / t_map[lvl]
            for lvl in sorted(t_map) if t_map[lvl] > 0
        }

    d_acc = _to_acc(deform_correct,  deform_total)
    e_acc = _to_acc_e(dirty_correct, dirty_total)
    return d_acc, e_acc


# ── main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("Step 5 — Model Evaluation")
    print("=" * 60)

    print(f"\nLoading model from {CKPT_PATH} …")
    model = load_model()

    print("Running inference on test set …")
    all_preds, all_labels, all_paths = run_inference(model)

    # ── sklearn classification report ─────────────────────────────────────────
    report = classification_report(
        all_labels, all_preds, target_names=CLASS_NAMES, digits=4
    )
    print("\nClassification Report:")
    print(report)

    # ── confusion matrix ──────────────────────────────────────────────────────
    plot_confusion_matrix(all_labels, all_preds)

    # ── WaDaBa group analysis ─────────────────────────────────────────────────
    d_acc, e_acc = wadaba_group_analysis(all_preds, all_labels, all_paths)

    deform_section = ""
    if d_acc:
        deform_section = "\n\nWaDaBa Accuracy by Deformation Level:\n"
        for k, v in sorted(d_acc.items()):
            deform_section += f"  {k}: {v*100:.2f}%\n"
        # Save JSON for step 7
        with open(RESULTS / "deformation_results.json", "w") as fh:
            json.dump(d_acc, fh, indent=2)
        print(deform_section)

    dirty_section = ""
    if e_acc:
        dirty_section = "\n\nWaDaBa Accuracy by Dirtiness Level:\n"
        for k, v in sorted(e_acc.items()):
            dirty_section += f"  {k}: {v*100:.2f}%\n"
        with open(RESULTS / "dirtiness_results.json", "w") as fh:
            json.dump(e_acc, fh, indent=2)
        print(dirty_section)

    # ── write full evaluation report ──────────────────────────────────────────
    report_path = RESULTS / "evaluation_report.txt"
    with open(report_path, "w") as fh:
        fh.write("=" * 60 + "\n")
        fh.write("Plastic Waste Classification — Evaluation Report\n")
        fh.write("=" * 60 + "\n\n")
        fh.write(f"Checkpoint: {CKPT_PATH}\n")
        fh.write(f"Test set:   {TEST_DIR}\n\n")
        fh.write("Classification Report:\n")
        fh.write(report)
        fh.write(deform_section)
        fh.write(dirty_section)

    print(f"\nEvaluation report saved → {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
