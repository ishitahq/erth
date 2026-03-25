"""
Step 4: Three-phase EfficientNet-B3 training pipeline.

Phase 1 — WaDaBa pre-training (frozen backbone)
  Dataset : dataset/wadaba_sorted/
  Epochs  : 15
  Optim   : Adam lr=1e-3
  Sched   : StepLR(step_size=5, gamma=0.5)
  Saves   : checkpoints/phase1_best.pth, logs/phase1_log.csv

Phase 2 — Unified fine-tuning (last 2 feature blocks unfrozen)
  Dataset : dataset/unified/
  Epochs  : 25
  Optim   : Adam lr=1e-4
  Sched   : StepLR(step_size=8, gamma=0.3)
  Saves   : checkpoints/phase2_best.pth, logs/phase2_log.csv

Phase 3 — Full fine-tuning (all layers unfrozen, early stopping)
  Dataset : dataset/unified/
  Epochs  : 30  (+ early stopping, patience=5 on val loss)
  Optim   : Adam lr=1e-5
  Sched   : CosineAnnealingLR(T_max=30)
  Saves   : checkpoints/phase3_best.pth, logs/phase3_log.csv

Hardware: GPU required (asserts torch.cuda.is_available()).

Run: python step4_train.py
"""

import csv
import json
import os
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Adam
from torch.optim.lr_scheduler import StepLR, CosineAnnealingLR
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import transforms
from torchvision.datasets import ImageFolder

try:
    from torchvision.models import efficientnet_b3, EfficientNet_B3_Weights
    def build_backbone() -> nn.Module:
        return efficientnet_b3(weights=EfficientNet_B3_Weights.DEFAULT)
except ImportError:
    import torchvision
    def build_backbone() -> nn.Module:          # type: ignore[misc]
        return torchvision.models.efficientnet_b3(pretrained=True)

from tqdm import tqdm

# ── GPU guard ─────────────────────────────────────────────────────────────────
assert torch.cuda.is_available(), (
    "CUDA GPU not found.  This pipeline requires a CUDA-capable GPU."
)
DEVICE = torch.device("cuda")

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
WADABA_DIR   = BASE_DIR / "dataset" / "wadaba_sorted"
UNIFIED_DIR  = BASE_DIR / "dataset" / "unified"
CKPT_DIR     = BASE_DIR / "checkpoints"
LOG_DIR      = BASE_DIR / "logs"
WEIGHTS_JSON = BASE_DIR / "class_weights.json"

CKPT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# ── constants ──────────────────────────────────────────────────────────────────
NUM_CLASSES  = 6
IMG_SIZE     = 300
NUM_WORKERS  = 4
PIN_MEMORY   = True

# ImageFolder sorts class names alphabetically:
# ['HDPE', 'LDPE', 'OTHER', 'PET', 'PP', 'PS']  (indices 0-5)
CLASS_NAMES = sorted(["HDPE", "LDPE", "OTHER", "PET", "PP", "PS"])

# ── transforms ────────────────────────────────────────────────────────────────
# Standard augmentation (majority classes: PET, OTHER)
TRAIN_TF = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(20),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
    transforms.RandomErasing(p=0.3, scale=(0.02, 0.2)),
])

# Heavier augmentation for minority classes (HDPE, LDPE, PS, PP)
# More rotation, stronger colour jitter, perspective distortion, higher erase prob
MINORITY_TF = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(35),
    transforms.ColorJitter(brightness=0.5, contrast=0.5, saturation=0.4, hue=0.1),
    transforms.RandomGrayscale(p=0.1),
    transforms.RandomPerspective(distortion_scale=0.3, p=0.4),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
    transforms.RandomErasing(p=0.5, scale=(0.02, 0.33)),
])

VAL_TF = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

# Minority class indices (alphabetical ImageFolder order):
# HDPE=0, LDPE=1, OTHER=2, PET=3, PP=4, PS=5
# Minority = all except the two largest (OTHER=2, PET=3)
MINORITY_CLASS_INDICES = {0, 1, 4, 5}  # HDPE, LDPE, PP, PS


class MinorityAwareDataset(ImageFolder):
    """ImageFolder that applies heavier augmentation to minority classes."""
    def __getitem__(self, index: int):
        path, label = self.samples[index]
        img = self.loader(path)
        tf = MINORITY_TF if label in MINORITY_CLASS_INDICES else TRAIN_TF
        return tf(img), label


# ── focal loss ───────────────────────────────────────────────────────────────
class FocalLoss(nn.Module):
    """
    Focal Loss: FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)

    gamma=2.0 (standard).  Class weights serve as alpha, same as weighted CE.
    Down-weights easy examples so training focuses on hard / minority cases.
    """
    def __init__(self, weight: torch.Tensor | None = None, gamma: float = 2.0) -> None:
        super().__init__()
        self.weight = weight
        self.gamma  = gamma

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        # Per-sample CE loss (unweighted first to get p_t)
        ce = F.cross_entropy(logits, targets, weight=self.weight, reduction="none")
        pt = torch.exp(-ce)                          # probability of correct class
        focal = ((1.0 - pt) ** self.gamma) * ce      # down-weight easy examples
        return focal.mean()


# ── model construction ────────────────────────────────────────────────────────
def build_model() -> nn.Module:
    """Return EfficientNet-B3 with a custom 6-class head."""
    model = build_backbone()
    # Replace the default classifier (1536→1000) with our head
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(1536, 512),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.2),
        nn.Linear(512, NUM_CLASSES),
    )
    return model.to(DEVICE)


# ── freeze / unfreeze helpers ─────────────────────────────────────────────────
def freeze_backbone(model: nn.Module) -> None:
    for param in model.features.parameters():
        param.requires_grad = False
    for param in model.classifier.parameters():
        param.requires_grad = True


def unfreeze_last_two_blocks(model: nn.Module) -> None:
    for param in model.features.parameters():
        param.requires_grad = False
    for param in model.features[-1].parameters():
        param.requires_grad = True
    for param in model.features[-2].parameters():
        param.requires_grad = True
    for param in model.classifier.parameters():
        param.requires_grad = True


def unfreeze_all(model: nn.Module) -> None:
    for param in model.parameters():
        param.requires_grad = True


# ── data loaders ──────────────────────────────────────────────────────────────
def make_loaders(
    root: Path,
    batch_size: int,
) -> tuple[DataLoader, DataLoader]:
    # MinorityAwareDataset applies heavier augmentation to minority classes.
    # transform arg is ignored — the dataset handles it internally.
    train_ds = MinorityAwareDataset(str(root / "train"))
    val_ds   = ImageFolder(str(root / "valid"), transform=VAL_TF)

    # ── WeightedRandomSampler ─────────────────────────────────────────────────
    # Gives each class equal expected frequency per batch, independent of
    # dataset size.  This works alongside FocalLoss (they address different
    # aspects: sampling frequency vs. gradient magnitude per example).
    class_counts = [0] * NUM_CLASSES
    for _, lbl in train_ds.samples:
        class_counts[lbl] += 1
    sample_weights = [
        1.0 / class_counts[lbl] for _, lbl in train_ds.samples
    ]
    sampler = WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(sample_weights),
        replacement=True,
    )

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, sampler=sampler,
        num_workers=NUM_WORKERS, pin_memory=PIN_MEMORY,
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False,
        num_workers=NUM_WORKERS, pin_memory=PIN_MEMORY,
    )
    return train_loader, val_loader


def load_class_weights() -> torch.Tensor:
    """Load balanced class weights into a CUDA tensor (alphabetical order)."""
    with open(WEIGHTS_JSON) as fh:
        w_dict: dict[str, float] = json.load(fh)
    return torch.tensor(
        [w_dict[cls] for cls in CLASS_NAMES], dtype=torch.float32
    ).to(DEVICE)


# ── CSV logger ────────────────────────────────────────────────────────────────
class CsvLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        with open(path, "w", newline="") as fh:
            csv.writer(fh).writerow(
                ["epoch", "train_loss", "train_acc", "val_loss", "val_acc", "lr"]
            )

    def log(self, epoch: int, tl: float, ta: float,
            vl: float, va: float, lr: float) -> None:
        with open(self.path, "a", newline="") as fh:
            csv.writer(fh).writerow(
                [epoch, f"{tl:.6f}", f"{ta:.4f}",
                 f"{vl:.6f}", f"{va:.4f}", f"{lr:.2e}"]
            )


# ── one epoch ─────────────────────────────────────────────────────────────────
def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer | None,
    training: bool,
) -> tuple[float, float]:
    """Return (avg_loss, accuracy)."""
    model.train(training)
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.set_grad_enabled(training):
        for imgs, labels in tqdm(loader, desc="  train" if training else "  val  ",
                                 leave=False, dynamic_ncols=True):
            imgs   = imgs.to(DEVICE, non_blocking=True)
            labels = labels.to(DEVICE, non_blocking=True)

            logits = model(imgs)
            loss   = criterion(logits, labels)

            if training and optimizer is not None:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            total_loss += loss.item() * imgs.size(0)
            correct    += (logits.argmax(1) == labels).sum().item()
            total      += imgs.size(0)

    return total_loss / total, correct / total


# ── training phase ────────────────────────────────────────────────────────────
def train_phase(
    phase_num:  int,
    model:      nn.Module,
    train_loader: DataLoader,
    val_loader:   DataLoader,
    criterion:  nn.Module,
    optimizer:  torch.optim.Optimizer,
    scheduler,
    num_epochs: int,
    ckpt_path:  Path,
    log_path:   Path,
    early_stop_patience: int | None = None,
) -> None:
    print(f"\n{'='*60}")
    print(f"Phase {phase_num}  —  {num_epochs} epochs")
    print(f"{'='*60}")

    logger     = CsvLogger(log_path)
    best_val   = float("inf")
    no_improve = 0

    for epoch in range(1, num_epochs + 1):
        train_loss, train_acc = run_epoch(
            model, train_loader, criterion, optimizer, training=True
        )
        val_loss, val_acc = run_epoch(
            model, val_loader, criterion, None, training=False
        )

        current_lr = optimizer.param_groups[0]["lr"]
        scheduler.step()

        logger.log(epoch, train_loss, train_acc, val_loss, val_acc, current_lr)

        print(
            f"  Epoch {epoch:3d}/{num_epochs}  "
            f"train_loss={train_loss:.4f}  train_acc={train_acc:.4f}  "
            f"val_loss={val_loss:.4f}  val_acc={val_acc:.4f}  lr={current_lr:.2e}"
        )

        # Save best checkpoint
        if val_loss < best_val:
            best_val = val_loss
            torch.save(model.state_dict(), ckpt_path)
            print(f"    ✓ Best model saved (val_loss={best_val:.4f})")
            no_improve = 0
        else:
            no_improve += 1

        # Early stopping
        if early_stop_patience is not None and no_improve >= early_stop_patience:
            print(f"  Early stopping triggered (no improvement for "
                  f"{early_stop_patience} epochs)")
            break

    print(f"Phase {phase_num} complete.  Best val_loss={best_val:.4f}")


# ── main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    cw = load_class_weights()
    # FocalLoss replaces plain CrossEntropyLoss.
    # Class weights act as alpha (handles inter-class frequency imbalance).
    # gamma=2.0 further concentrates gradient on hard / minority examples.
    criterion = FocalLoss(weight=cw, gamma=2.0)

    # ── Phase 1: WaDaBa only, frozen backbone ─────────────────────────────────
    model = build_model()
    freeze_backbone(model)

    train_loader1, val_loader1 = make_loaders(WADABA_DIR, batch_size=32)
    opt1   = Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-3)
    sched1 = StepLR(opt1, step_size=5, gamma=0.5)

    train_phase(
        phase_num=1,
        model=model,
        train_loader=train_loader1,
        val_loader=val_loader1,
        criterion=criterion,
        optimizer=opt1,
        scheduler=sched1,
        num_epochs=15,
        ckpt_path=CKPT_DIR / "phase1_best.pth",
        log_path=LOG_DIR / "phase1_log.csv",
    )

    # ── Phase 2: Unified, last 2 blocks unfrozen ──────────────────────────────
    model.load_state_dict(torch.load(CKPT_DIR / "phase1_best.pth"))
    unfreeze_last_two_blocks(model)

    train_loader2, val_loader2 = make_loaders(UNIFIED_DIR, batch_size=32)
    opt2   = Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-4)
    sched2 = StepLR(opt2, step_size=8, gamma=0.3)

    train_phase(
        phase_num=2,
        model=model,
        train_loader=train_loader2,
        val_loader=val_loader2,
        criterion=criterion,
        optimizer=opt2,
        scheduler=sched2,
        num_epochs=25,
        ckpt_path=CKPT_DIR / "phase2_best.pth",
        log_path=LOG_DIR / "phase2_log.csv",
    )

    # ── Phase 3: Unified, full fine-tuning, early stopping ───────────────────
    model.load_state_dict(torch.load(CKPT_DIR / "phase2_best.pth"))
    unfreeze_all(model)

    train_loader3, val_loader3 = make_loaders(UNIFIED_DIR, batch_size=16)
    opt3   = Adam(model.parameters(), lr=1e-5)
    sched3 = CosineAnnealingLR(opt3, T_max=30)

    train_phase(
        phase_num=3,
        model=model,
        train_loader=train_loader3,
        val_loader=val_loader3,
        criterion=criterion,
        optimizer=opt3,
        scheduler=sched3,
        num_epochs=30,
        ckpt_path=CKPT_DIR / "phase3_best.pth",
        log_path=LOG_DIR  / "phase3_log.csv",
        early_stop_patience=5,
    )

    print("\nAll three phases complete.")
    print(f"Final checkpoint: {CKPT_DIR / 'phase3_best.pth'}")


if __name__ == "__main__":
    main()
