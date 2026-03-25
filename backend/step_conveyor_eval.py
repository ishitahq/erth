"""
Conveyor Belt Real-World Evaluation
=====================================
Evaluates checkpoints/phase3_best.pth on the conveyor belt dataset.
This dataset is used ONLY for testing — never for training.

Dataset layout:
  conveyor/img/           ← 95 labeled JPEG images (640×640)
  conveyor/labels/        ← Pascal VOC XML files with bounding boxes
  conveyor/additional_images/ ← unlabeled, ignored

Class mapping:
  mix PP    → PP
  mix HD    → HDPE
  mix PET   → PET
  mix rigid → OTHER

Outputs (all in results/):
  conveyor_eval_report.txt
  conveyor_confusion_matrix.png
  conveyor_sample_predictions.png
  conveyor_confidence_distribution.png
  conveyor_annotated_images/  ← per-image bounding-box overlay

Run: python step_conveyor_eval.py
"""

import os
import re
import random
import warnings
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageDraw, ImageFont
from torchvision import transforms
from tqdm import tqdm

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix

# ── GPU guard ──────────────────────────────────────────────────────────────────
assert torch.cuda.is_available(), (
    "CUDA GPU is required for conveyor evaluation."
)
DEVICE = torch.device("cuda")
print(f"Device: {torch.cuda.get_device_name(0)}")

# ── paths ──────────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
CKPT_PATH       = BASE_DIR / "checkpoints" / "phase3_best.pth"
CONVEYOR_IMG    = BASE_DIR / "dataset" / "conveyor" / "img"
CONVEYOR_LABELS = BASE_DIR / "dataset" / "conveyor" / "labels"
RESULTS         = BASE_DIR / "results"
ANNOTATED_DIR   = RESULTS / "conveyor_annotated_images"
EVAL_REPORT_TXT = BASE_DIR / "results" / "evaluation_report.txt"

RESULTS.mkdir(exist_ok=True)
ANNOTATED_DIR.mkdir(exist_ok=True)

# ── constants ──────────────────────────────────────────────────────────────────
NUM_CLASSES       = 6
IMG_SIZE          = 300
CONF_THRESHOLD    = 0.70
CLASS_NAMES       = sorted(["HDPE", "LDPE", "OTHER", "PET", "PP", "PS"])
CLASS_TO_IDX      = {c: i for i, c in enumerate(CLASS_NAMES)}

CONVEYOR_CLASS_MAP = {
    "mix pp":    "PP",
    "mix hd":    "HDPE",
    "mix hdpe":  "HDPE",
    "mix pet":   "PET",
    "mix rigid": "OTHER",
}

# ── inference transform (no augmentation) ─────────────────────────────────────
INFER_TF = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


# ── model ─────────────────────────────────────────────────────────────────────
def build_model() -> nn.Module:
    try:
        from torchvision.models import efficientnet_b3, EfficientNet_B3_Weights
        model = efficientnet_b3(weights=None)
    except ImportError:
        import torchvision
        model = torchvision.models.efficientnet_b3(pretrained=False)

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


# ── XML parsing ───────────────────────────────────────────────────────────────
def parse_xml(xml_path: Path) -> list[dict]:
    """
    Parse a Pascal VOC XML file and return a list of annotation dicts:
      [{"class": "PP", "box": (xmin, ymin, xmax, ymax)}, ...]
    Returns an empty list on parse failure (logs a warning).
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as exc:
        warnings.warn(f"Malformed XML skipped: {xml_path}  ({exc})")
        return []

    objects = []
    for obj in root.findall("object"):
        raw_name = (obj.findtext("name") or "").strip().lower()
        target_class = CONVEYOR_CLASS_MAP.get(raw_name)
        if target_class is None:
            warnings.warn(f"Unknown class '{raw_name}' in {xml_path}, skipping object.")
            continue

        bndbox = obj.find("bndbox")
        if bndbox is None:
            continue
        try:
            xmin = int(float(bndbox.findtext("xmin")))
            ymin = int(float(bndbox.findtext("ymin")))
            xmax = int(float(bndbox.findtext("xmax")))
            ymax = int(float(bndbox.findtext("ymax")))
        except (TypeError, ValueError):
            warnings.warn(f"Bad bndbox values in {xml_path}, skipping object.")
            continue

        objects.append({"class": target_class, "box": (xmin, ymin, xmax, ymax)})
    return objects


def find_xml_for_image(img_path: Path) -> Path | None:
    """
    Look for a matching XML in CONVEYOR_LABELS.
    Tries exact stem match first, then a case-insensitive search.
    """
    stem = img_path.stem
    # exact match
    candidate = CONVEYOR_LABELS / (stem + ".xml")
    if candidate.exists():
        return candidate
    # case-insensitive fallback
    stem_lower = stem.lower()
    for xml_file in CONVEYOR_LABELS.glob("*.xml"):
        if xml_file.stem.lower() == stem_lower:
            return xml_file
    return None


# ── inference on a single crop ────────────────────────────────────────────────
@torch.no_grad()
def predict_crop(model: nn.Module, crop: Image.Image) -> tuple[str, float]:
    """Returns (predicted_class_or_Unknown, confidence)."""
    if crop.width < 2 or crop.height < 2:
        return "Unknown", 0.0
    tensor = INFER_TF(crop.convert("RGB")).unsqueeze(0).to(DEVICE)
    logits = model(tensor)
    probs  = torch.softmax(logits, dim=1).squeeze(0).cpu().tolist()
    conf   = max(probs)
    pred_idx = probs.index(conf)
    if conf < CONF_THRESHOLD:
        return "Unknown", conf
    return CLASS_NAMES[pred_idx], conf


# ── draw annotated image ──────────────────────────────────────────────────────
def save_annotated_image(
    img: Image.Image,
    annotations: list[dict],
    predictions: list[tuple[str, float]],
    out_path: Path,
) -> None:
    """Draw bounding boxes on img and save. Green = correct, Red = wrong."""
    draw = ImageDraw.Draw(img.copy())
    result_img = img.copy()
    draw = ImageDraw.Draw(result_img)

    try:
        font = ImageFont.truetype("arial.ttf", size=12)
    except OSError:
        font = ImageFont.load_default()

    for ann, (pred_class, conf) in zip(annotations, predictions):
        gt   = ann["class"]
        box  = ann["box"]
        correct = (pred_class == gt)
        color = "#00cc44" if correct else "#ff3333"   # green / red

        draw.rectangle(box, outline=color, width=2)
        label = f"GT:{gt}|P:{pred_class}|{conf*100:.0f}%"

        # draw label background
        bbox_text = draw.textbbox((box[0], box[1] - 15), label, font=font)
        draw.rectangle(bbox_text, fill=color)
        draw.text((box[0], box[1] - 15), label, fill="white", font=font)

    result_img.save(out_path)


# ── load clean-test accuracy from existing report ────────────────────────────
def load_clean_accuracy() -> float | None:
    if not EVAL_REPORT_TXT.exists():
        return None
    text = EVAL_REPORT_TXT.read_text(encoding="utf-8", errors="ignore")
    # look for "accuracy   …   0.XXXX" line in sklearn report
    m = re.search(r"accuracy\s+(\d+\.\d+)\s+\d+", text)
    if m:
        return float(m.group(1)) * 100.0
    return None


# ── confidence distribution from clean test ──────────────────────────────────
def collect_clean_confidences(model: nn.Module) -> list[float]:
    """Run model on unified/test/ and collect max-softmax confidence per sample."""
    test_dir = BASE_DIR / "dataset" / "unified" / "test"
    if not test_dir.exists():
        return []

    from torchvision.datasets import ImageFolder
    from torch.utils.data import DataLoader

    ds     = ImageFolder(str(test_dir), transform=INFER_TF)
    loader = DataLoader(ds, batch_size=64, shuffle=False,
                        num_workers=0, pin_memory=True)
    confs  = []
    with torch.no_grad():
        for imgs, _ in tqdm(loader, desc="Clean-test confidences", leave=False):
            imgs  = imgs.to(DEVICE, non_blocking=True)
            probs = torch.softmax(model(imgs), dim=1)
            confs.extend(probs.max(dim=1).values.cpu().tolist())
    return confs


# ── confusion matrix plot ─────────────────────────────────────────────────────
def plot_confusion_matrix(
    y_true_names: list[str],
    y_pred_names: list[str],
    labels: list[str],
    title: str,
    out_path: Path,
) -> None:
    label_set = sorted(set(y_true_names) | set(y_pred_names) - {"Unknown"})
    # keep only classes present in GT
    gt_classes = sorted(set(y_true_names))
    cm = confusion_matrix(y_true_names, y_pred_names, labels=gt_classes)
    cm_norm = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)

    n = len(gt_classes)
    fig, ax = plt.subplots(figsize=(max(6, n), max(5, n - 1)))
    img = ax.imshow(cm_norm, interpolation="nearest", cmap="Blues",
                    vmin=0.0, vmax=1.0)
    plt.colorbar(img, ax=ax)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(gt_classes, rotation=45, ha="right")
    ax.set_yticklabels(gt_classes)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)

    for i in range(n):
        for j in range(n):
            ax.text(j, i, f"{cm_norm[i, j]:.2f}",
                    ha="center", va="center",
                    color="white" if cm_norm[i, j] > 0.5 else "black",
                    fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Confusion matrix saved → {out_path}")


# ── sample predictions grid ──────────────────────────────────────────────────
def plot_sample_predictions(
    crop_records: list[dict],
    out_path: Path,
) -> None:
    """Pick 3 crops per present class (up to 12 total) and show a 3×4 grid."""
    by_class: dict[str, list[dict]] = defaultdict(list)
    for rec in crop_records:
        by_class[rec["gt"]].append(rec)

    target_classes = ["PP", "HDPE", "PET", "OTHER"]
    samples: list[dict] = []
    for cls in target_classes:
        pool = by_class.get(cls, [])
        random.shuffle(pool)
        samples.extend(pool[:3])

    if not samples:
        return

    cols, rows = 4, 3
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 3, rows * 3))
    axes_flat = axes.flatten()

    for i, ax in enumerate(axes_flat):
        ax.axis("off")
        if i >= len(samples):
            continue
        rec  = samples[i]
        crop = rec["crop_pil"]
        gt   = rec["gt"]
        pred = rec["pred"]
        conf = rec["conf"]

        ax.imshow(crop)
        color = "green" if pred == gt else "red"
        ax.set_title(f"GT: {gt} | Pred: {pred} | {conf*100:.1f}%",
                     color=color, fontsize=8, fontweight="bold")

    fig.suptitle("Conveyor Belt Sample Predictions (3 per class)", fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Sample predictions saved → {out_path}")


# ── confidence distribution plot ─────────────────────────────────────────────
def plot_confidence_distribution(
    clean_confs: list[float],
    conveyor_confs: list[float],
    out_path: Path,
) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), sharey=False)
    bins = np.linspace(0, 1, 21)

    ax1.hist(clean_confs, bins=bins, color="#4c78a8", edgecolor="white", linewidth=0.4)
    ax1.axvline(CONF_THRESHOLD, color="red", linestyle="--", linewidth=1.2,
                label=f"Threshold {CONF_THRESHOLD}")
    ax1.set_title("Clean Test Set")
    ax1.set_xlabel("Max Softmax Confidence")
    ax1.set_ylabel("Count")
    ax1.legend(fontsize=8)

    ax2.hist(conveyor_confs, bins=bins, color="#f58518", edgecolor="white", linewidth=0.4)
    ax2.axvline(CONF_THRESHOLD, color="red", linestyle="--", linewidth=1.2,
                label=f"Threshold {CONF_THRESHOLD}")
    ax2.set_title("Conveyor Belt (Real-World)")
    ax2.set_xlabel("Max Softmax Confidence")
    ax2.set_ylabel("Count")
    ax2.legend(fontsize=8)

    fig.suptitle("Confidence Distribution: Clean vs Real-World", fontsize=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Confidence distribution saved → {out_path}")


# ── main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    random.seed(42)
    model = build_model()
    print(f"Model loaded from {CKPT_PATH}")

    # Collect all labeled images
    img_files = sorted(CONVEYOR_IMG.glob("*.jp*g")) + sorted(CONVEYOR_IMG.glob("*.JP*G"))
    # deduplicate by stem (case-insensitive)
    seen_stems: set[str] = set()
    unique_imgs: list[Path] = []
    for p in img_files:
        if p.stem.lower() not in seen_stems:
            seen_stems.add(p.stem.lower())
            unique_imgs.append(p)
    img_files = unique_imgs

    # Per-class accumulators
    per_class_gt:   dict[str, int]   = defaultdict(int)
    per_class_ok:   dict[str, int]   = defaultdict(int)
    per_class_conf: dict[str, list]  = defaultdict(list)

    correct_confs: list[float]  = []
    wrong_confs:   list[float]  = []
    unknown_count: int          = 0
    conveyor_confs: list[float] = []

    all_gt_names:   list[str] = []
    all_pred_names: list[str] = []

    crop_records: list[dict] = []   # for sample-prediction grid

    images_evaluated = 0
    total_crops      = 0

    for img_path in tqdm(img_files, desc="Evaluating images"):
        xml_path = find_xml_for_image(img_path)
        if xml_path is None:
            warnings.warn(f"No XML found for {img_path.name}, skipping.")
            continue

        annotations = parse_xml(xml_path)
        if not annotations:
            continue

        try:
            pil_img = Image.open(img_path).convert("RGB")
        except Exception as exc:
            warnings.warn(f"Cannot open {img_path.name}: {exc}, skipping.")
            continue

        images_evaluated += 1
        predictions: list[tuple[str, float]] = []

        for ann in annotations:
            gt   = ann["class"]
            box  = ann["box"]
            xmin, ymin, xmax, ymax = box

            # Clamp box to image dimensions
            w, h = pil_img.size
            xmin = max(0, min(xmin, w - 1))
            xmax = max(xmin + 1, min(xmax, w))
            ymin = max(0, min(ymin, h - 1))
            ymax = max(ymin + 1, min(ymax, h))

            crop = pil_img.crop((xmin, ymin, xmax, ymax))
            pred_class, conf = predict_crop(model, crop)

            predictions.append((pred_class, conf))
            conveyor_confs.append(conf)
            total_crops += 1

            per_class_gt[gt] += 1
            per_class_conf[gt].append(conf)

            if pred_class == "Unknown":
                unknown_count += 1
                all_gt_names.append(gt)
                all_pred_names.append("Unknown")
                wrong_confs.append(conf)
            else:
                all_gt_names.append(gt)
                all_pred_names.append(pred_class)
                if pred_class == gt:
                    per_class_ok[gt] += 1
                    correct_confs.append(conf)
                else:
                    wrong_confs.append(conf)

            crop_records.append({
                "image":    img_path.name,
                "gt":       gt,
                "pred":     pred_class,
                "conf":     conf,
                "crop_pil": crop,
            })

        # Save annotated image
        ann_out = ANNOTATED_DIR / img_path.name
        save_annotated_image(pil_img, annotations, predictions, ann_out)

    # ── metrics ───────────────────────────────────────────────────────────────
    overall_correct = sum(
        1 for g, p in zip(all_gt_names, all_pred_names) if g == p
    )
    overall_acc = (overall_correct / total_crops * 100) if total_crops else 0.0
    avg_conf_correct = np.mean(correct_confs) * 100 if correct_confs else 0.0
    avg_conf_wrong   = np.mean(wrong_confs)   * 100 if wrong_confs   else 0.0
    unknown_pct      = (unknown_count / total_crops * 100) if total_crops else 0.0

    # ── comparison vs clean test set ─────────────────────────────────────────
    clean_acc = load_clean_accuracy()
    acc_drop  = (clean_acc - overall_acc) if clean_acc is not None else None

    clean_confs = collect_clean_confidences(model)
    avg_clean_conf    = np.mean(clean_confs)    * 100 if clean_confs    else 0.0
    avg_conveyor_conf = np.mean(conveyor_confs) * 100 if conveyor_confs else 0.0
    conf_drop = avg_clean_conf - avg_conveyor_conf

    # ── write report ──────────────────────────────────────────────────────────
    report_lines: list[str] = []
    w = report_lines.append

    w("Conveyor Belt Real-World Evaluation")
    w("=====================================")
    w(f"Total images evaluated     : {images_evaluated}")
    w(f"Total bounding box crops   : {total_crops}")
    w(f"Overall crop accuracy      : {overall_acc:.1f}%")
    w("")
    w("Per-class Results:")
    header = f"  {'Class':<10} {'GT crops':>10} {'Correct':>9} {'Accuracy':>10} {'Avg Confidence':>16}"
    w(header)
    w("  " + "-" * (len(header) - 2))

    conveyor_classes = ["PP", "HDPE", "PET", "OTHER"]
    for cls in conveyor_classes:
        gt_n  = per_class_gt.get(cls, 0)
        ok_n  = per_class_ok.get(cls, 0)
        acc_c = (ok_n / gt_n * 100) if gt_n else 0.0
        cf    = (np.mean(per_class_conf[cls]) * 100) if per_class_conf[cls] else 0.0
        w(f"  {cls:<10} {gt_n:>10} {ok_n:>9} {acc_c:>9.1f}% {cf:>14.1f}%")

    w("")
    w("Confidence Analysis:")
    w(f"  Average confidence (correct predictions)   : {avg_conf_correct:.1f}%")
    w(f"  Average confidence (wrong predictions)     : {avg_conf_wrong:.1f}%")
    w(f"  Crops flagged as Unknown (conf < {CONF_THRESHOLD:.2f})     : {unknown_count} ({unknown_pct:.1f}%)")

    w("")
    w("Comparison vs Clean Test Set:")
    if clean_acc is not None:
        w(f"  Clean test accuracy    : {clean_acc:.1f}%   (from results/evaluation_report.txt)")
    else:
        w("  Clean test accuracy    : N/A  (results/evaluation_report.txt not found)")
    w(f"  Conveyor accuracy      : {overall_acc:.1f}%")
    if acc_drop is not None:
        w(f"  Accuracy drop          : {acc_drop:.1f}%   (expected — real world is harder)")
    else:
        w("  Accuracy drop          : N/A")
    w(f"  Confidence drop        : {conf_drop:.1f}%")

    report_text = "\n".join(report_lines)
    report_path = RESULTS / "conveyor_eval_report.txt"
    report_path.write_text(report_text, encoding="utf-8")
    print(f"\nReport saved → {report_path}")
    print()
    print(report_text)

    # ── visualizations ────────────────────────────────────────────────────────
    # 1. Confusion matrix (exclude Unknown from GT axis)
    gt_for_cm   = [g for g, p in zip(all_gt_names, all_pred_names) if g != "Unknown"]
    pred_for_cm = [p for g, p in zip(all_gt_names, all_pred_names) if g != "Unknown"]
    if gt_for_cm:
        plot_confusion_matrix(
            gt_for_cm, pred_for_cm,
            labels=conveyor_classes,
            title="Conveyor Belt — Confusion Matrix",
            out_path=RESULTS / "conveyor_confusion_matrix.png",
        )

    # 2. Sample predictions grid
    plot_sample_predictions(crop_records, RESULTS / "conveyor_sample_predictions.png")

    # 3. Confidence distribution
    plot_confidence_distribution(
        clean_confs, conveyor_confs,
        RESULTS / "conveyor_confidence_distribution.png",
    )

    # ── one-line summary ──────────────────────────────────────────────────────
    if clean_acc is not None and acc_drop is not None:
        print(
            f"\nConveyor Real-World Test: {overall_acc:.1f}% crop accuracy on "
            f"{total_crops} crops from {images_evaluated} industrial images\n"
            f"(vs {clean_acc:.1f}% on clean test set — {acc_drop:.1f}% domain gap)"
        )
    else:
        print(
            f"\nConveyor Real-World Test: {overall_acc:.1f}% crop accuracy on "
            f"{total_crops} crops from {images_evaluated} industrial images"
        )


if __name__ == "__main__":
    main()
