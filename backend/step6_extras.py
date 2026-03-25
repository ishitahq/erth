"""
Step 6: Extras — Grad-CAM visualisation, confidence threshold rejection, ONNX export.

1. Grad-CAM
   - Target layer: model.features[-1]
   - 10 random test images
   - Side-by-side original | CAM overlay saved to results/gradcam/sample_{N}.png

2. Confidence Threshold (0.70)
   - Images where max softmax probability < 0.70 → flagged as "Unknown — Flag for Review"
   - Per-class flagging stats saved to results/confidence_report.txt

3. ONNX Export
   - Opset 11, input shape (1, 3, 300, 300)
   - Verified with onnxruntime
   - Saved to results/plastic_classifier.onnx

Hardware: GPU required.
Requires: pip install pytorch-grad-cam onnx onnxruntime

Run: python step6_extras.py
"""

import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.datasets import ImageFolder
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# pytorch-grad-cam
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
from pytorch_grad_cam.utils.image import show_cam_on_image

# ONNX
import onnx
import onnxruntime as ort

try:
    from torchvision.models import efficientnet_b3, EfficientNet_B3_Weights
    def build_backbone() -> nn.Module:
        return efficientnet_b3(weights=EfficientNet_B3_Weights.DEFAULT)
except ImportError:
    import torchvision
    def build_backbone() -> nn.Module:          # type: ignore[misc]
        return torchvision.models.efficientnet_b3(pretrained=False)

# ── GPU guard ─────────────────────────────────────────────────────────────────
assert torch.cuda.is_available(), "CUDA GPU is required."
DEVICE = torch.device("cuda")

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
CKPT_PATH  = BASE_DIR / "checkpoints" / "phase3_best.pth"
TEST_DIR   = BASE_DIR / "dataset" / "unified" / "test"
RESULTS    = BASE_DIR / "results"
GRADCAM_DIR = RESULTS / "gradcam"
RESULTS.mkdir(exist_ok=True)
GRADCAM_DIR.mkdir(exist_ok=True)

NUM_CLASSES       = 6
IMG_SIZE          = 300
NUM_WORKERS       = 4
CONFIDENCE_THRESH = 0.70
N_GRADCAM_IMAGES  = 10

CLASS_NAMES = sorted(["HDPE", "LDPE", "OTHER", "PET", "PP", "PS"])

IMG_MEAN = [0.485, 0.456, 0.406]
IMG_STD  = [0.229, 0.224, 0.225]

VAL_TF = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMG_MEAN, std=IMG_STD),
])

# Un-normalise for display (RGB float 0-1)
UNNORM_MEAN = torch.tensor(IMG_MEAN).view(3, 1, 1)
UNNORM_STD  = torch.tensor(IMG_STD).view(3, 1, 1)


def unnormalise(tensor: torch.Tensor) -> np.ndarray:
    """Return (H, W, 3) float32 array in [0, 1]."""
    img = tensor.cpu() * UNNORM_STD + UNNORM_MEAN
    img = img.clamp(0, 1).permute(1, 2, 0).numpy().astype(np.float32)
    return img


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


# ── dataset with paths ────────────────────────────────────────────────────────
class ImageFolderWithPaths(ImageFolder):
    def __getitem__(self, index):
        img, label = super().__getitem__(index)
        path = self.samples[index][0]
        return img, label, path


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Grad-CAM
# ═══════════════════════════════════════════════════════════════════════════════
def run_gradcam(model: nn.Module) -> None:
    print("\n[1/3] Generating Grad-CAM visualisations …")

    ds = ImageFolderWithPaths(str(TEST_DIR), transform=VAL_TF)
    indices = random.sample(range(len(ds)), min(N_GRADCAM_IMAGES, len(ds)))

    target_layers = [model.features[-1]]

    # GradCAM context manager handles hooks safely
    with GradCAM(model=model, target_layers=target_layers) as cam:
        for sample_idx, ds_idx in enumerate(indices, start=1):
            img_tensor, label, path = ds[ds_idx]
            input_batch = img_tensor.unsqueeze(0).to(DEVICE)

            # Use the true class as the CAM target
            targets = [ClassifierOutputTarget(label)]
            grayscale_cam = cam(input_tensor=input_batch, targets=targets)
            grayscale_map = grayscale_cam[0]  # (H, W)

            rgb_img = unnormalise(img_tensor)
            overlay = show_cam_on_image(rgb_img, grayscale_map, use_rgb=True)

            fig, axes = plt.subplots(1, 2, figsize=(8, 4))
            axes[0].imshow(rgb_img)
            axes[0].set_title(f"Original\nTrue: {CLASS_NAMES[label]}")
            axes[0].axis("off")

            axes[1].imshow(overlay)
            axes[1].set_title("Grad-CAM overlay")
            axes[1].axis("off")

            fig.suptitle(Path(path).name, fontsize=7)
            fig.tight_layout()
            out = GRADCAM_DIR / f"sample_{sample_idx}.png"
            fig.savefig(out, dpi=120)
            plt.close(fig)
            print(f"  Saved {out}")

    print(f"Grad-CAM images saved to {GRADCAM_DIR}")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Confidence Threshold
# ═══════════════════════════════════════════════════════════════════════════════
def run_confidence_analysis(model: nn.Module) -> None:
    print(f"\n[2/3] Confidence threshold analysis (threshold={CONFIDENCE_THRESH}) …")

    ds = ImageFolderWithPaths(str(TEST_DIR), transform=VAL_TF)
    loader = DataLoader(
        ds, batch_size=32, shuffle=False,
        num_workers=NUM_WORKERS, pin_memory=True,
    )

    flagged_per_class   = {cls: 0 for cls in CLASS_NAMES}
    total_per_class     = {cls: 0 for cls in CLASS_NAMES}
    total_flagged       = 0
    total_images        = 0
    softmax             = nn.Softmax(dim=1)

    with torch.no_grad():
        for imgs, labels, _ in loader:
            imgs   = imgs.to(DEVICE, non_blocking=True)
            logits = model(imgs)
            probs  = softmax(logits)
            max_p, _ = probs.max(dim=1)

            for i, (p, lbl) in enumerate(zip(max_p.cpu().tolist(),
                                              labels.tolist())):
                cls = CLASS_NAMES[lbl]
                total_per_class[cls] += 1
                total_images += 1
                if p < CONFIDENCE_THRESH:
                    flagged_per_class[cls] += 1
                    total_flagged += 1

    report_lines = [
        "=" * 60,
        f"Confidence Threshold Report  (threshold = {CONFIDENCE_THRESH})",
        "=" * 60,
        "",
        f"{'Class':<8} {'Total':>7} {'Flagged':>9} {'Flag%':>8}",
        "-" * 40,
    ]
    for cls in CLASS_NAMES:
        tot = total_per_class[cls]
        flg = flagged_per_class[cls]
        pct = (flg / tot * 100) if tot else 0.0
        report_lines.append(f"{cls:<8} {tot:>7} {flg:>9} {pct:>7.2f}%")

    report_lines += [
        "-" * 40,
        f"{'TOTAL':<8} {total_images:>7} {total_flagged:>9} "
        f"{total_flagged/total_images*100:>7.2f}%",
        "",
        "Images below threshold are flagged as: Unknown — Flag for Review",
    ]

    report_text = "\n".join(report_lines)
    print(report_text)

    out = RESULTS / "confidence_report.txt"
    out.write_text(report_text, encoding="utf-8")
    print(f"\nConfidence report saved → {out}")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ONNX Export
# ═══════════════════════════════════════════════════════════════════════════════
def export_onnx(model: nn.Module) -> None:
    print("\n[3/3] Exporting model to ONNX …")

    onnx_path = RESULTS / "plastic_classifier.onnx"
    dummy_input = torch.randn(1, 3, IMG_SIZE, IMG_SIZE, device=DEVICE)

    # Export with dropout disabled (eval mode already set)
    torch.onnx.export(
        model,
        dummy_input,
        str(onnx_path),
        opset_version=11,
        input_names=["image"],
        output_names=["logits"],
        dynamic_axes={"image": {0: "batch_size"}, "logits": {0: "batch_size"}},
        verbose=False,
    )

    # Validate ONNX model structure
    onnx_model = onnx.load(str(onnx_path))
    onnx.checker.check_model(onnx_model)
    print("  ONNX model structure — OK")

    # Verify with onnxruntime
    sess = ort.InferenceSession(str(onnx_path),
                                providers=["CUDAExecutionProvider",
                                           "CPUExecutionProvider"])
    dummy_np = dummy_input.cpu().numpy()
    ort_out   = sess.run(None, {"image": dummy_np})
    torch_out = model(dummy_input).detach().cpu().numpy()

    max_diff = float(np.abs(ort_out[0] - torch_out).max())
    print(f"  onnxruntime vs PyTorch max output diff: {max_diff:.6f}")
    assert max_diff < 1e-2, f"ONNX verification failed: diff={max_diff}"
    print(f"  ONNX verification — OK")
    print(f"  Saved → {onnx_path}")


# ── main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("Step 6 — Extras: Grad-CAM / Confidence / ONNX")
    print("=" * 60)

    model = load_model()

    run_gradcam(model)
    run_confidence_analysis(model)
    export_onnx(model)

    print("\nStep 6 complete.")


if __name__ == "__main__":
    main()
