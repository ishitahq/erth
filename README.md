# ♻️ Erth — Robust AI System for Plastic Waste Analysis

Erth is a **multi-stage AI perception system** designed for real-world plastic waste processing. It goes beyond simple classification by combining **deep learning, zero-shot reasoning, depth estimation, and object detection** to enable intelligent recycling pipelines.

> **Core Idea:** Not just classify plastic — *understand it, evaluate it, and quantify it*.

---

## 🌍 Problem Overview

Plastic recycling systems depend heavily on **accurate material identification**, but real-world conditions introduce major challenges:
* Dirty, deformed, and overlapping waste
* Inconsistent lighting and motion blur
* Visually similar polymer types
* Severe **domain gap** between lab data and industrial conveyor environments

Misclassification leads to:
* Contaminated recycling streams
* Reduced material quality
* Economic loss

---

## System Overview

Erth is designed as a **multi-stage pipeline**, where each stage solves a specific sub-problem:

```
Image → Type Classification → Recyclability Grading → Volume Estimation → Detection → Structured Output
```

---

## 🏗️ Architecture

<img width="2048" height="1117" alt="image" src="https://github.com/user-attachments/assets/e0b8c3c8-ea59-49db-b884-930d82088ac9" />


### Training Pipeline
* Dual dataset integration (**TIP + WaDaBa**)
* Label normalization (collapse noisy labels → 6 classes)
* Class imbalance handling (5× skew)
* Progressive training strategy (3-phase fine-tuning)

### Inference Pipeline
* EfficientNet-based classification
* CLIP-based grading
* Depth-based volume estimation
* YOLOv8 multi-object detection
* Structured JSON outputs

---

## Dataset Strategy

### TIP (Trash Image Project)
* Pascal VOC XML annotations
* Noisy labels → normalized to 6 classes

### WaDaBa (Waste Database Bavaria)
* Filename-encoded labels
* Includes **deformation (d0–d3)** and **dirtiness (e0–e3)** metadata

### Unified Dataset
* Combined and balanced dataset
* Class weights computed (up to **5.15× imbalance**)

---

## Model Design

### Backbone: EfficientNet-B3
* 300×300 input resolution
* Compound scaling (better accuracy per FLOP)
* Custom classifier head with dropout for regularization

---

## ⚙️ Training Strategy (Core Innovation)

### 3-Phase Progressive Fine-Tuning

| Phase   | Description                    | Purpose                           |
| ------- | ------------------------------ | --------------------------------- |
| Phase 1 | Frozen backbone, WaDaBa only   | Learn clean class representations |
| Phase 2 | Partial unfreeze, unified data | Adapt to noisy + diverse data     |
| Phase 3 | Full fine-tuning with SAM      | Improve real-world generalization |

---

### Advanced Optimization

#### Focal Loss (γ = 2)
* Focuses learning on hard examples
* Handles minority classes (LDPE, PS)

#### Weighted Random Sampling
* Ensures balanced batch composition

#### Sharpness-Aware Minimization (SAM)
* Avoids sharp minima
* Improves robustness to domain shift

---

## Augmentation Strategy
Designed to simulate real conveyor conditions:
* CLAHE (contrast normalization)
* Rotation (±45°), flips
* Motion blur simulation
* Color jitter (lighting variation)
* Grayscale (texture learning)
* Occlusion (CoarseDropout)

---

## 📊 Performance

### Clean Test Set

**Accuracy:** 98.77%

| Class | F1 Score |
| ----- | -------- |
| LDPE  | 1.00     |
| OTHER | 1.00     |
| PET   | 0.98     |
| HDPE  | 0.99     |
| PP    | 0.97     |
| PS    | 0.96     |

---

### Real-World Conveyor Performance

| Metric              | Value |
| ------------------- | ----- |
| Accuracy            | 40.7% |
| Confidence Drop     | 27.3% |
| Unknown Predictions | 58%   |

👉 Reveals a **57.5% domain gap**

---

## Domain Shift Analysis (Key Insight)
The major challenge is the difference between:

| Lab Data            | Conveyor Data                |
| ------------------- | ---------------------------- |
| Clean background    | Complex background           |
| Single object       | Multiple overlapping objects |
| Well-lit            | Industrial lighting          |
| Minimal deformation | Heavy deformation            |

---

## 🛠️ Mitigation Techniques
* Sharpness-aware training (SAM)
* Test-Time Augmentation (8-view averaging)
* CLAHE normalization
* Robust augmentation pipeline

---

## Inference Pipeline

### Stage 1 — Plastic Type
* EfficientNet-B3
* Outputs: `{type, confidence}`
* Unknown if confidence < 0.70

### Stage 2 — Recyclability Grade (CLIP)
* Zero-shot classification
* No labeled dataset required

| Grade | Meaning             |
| ----- | ------------------- |
| A     | Clean, recyclable   |
| B     | Needs preprocessing |
| C     | Reject              |

### Stage 3 — Volume Estimation
* Depth Anything V2
* Uses monocular depth + geometry

### Stage 4 — Detection
* YOLOv8-nano
* Multi-object detection on conveyor frames

---

## Output Format

```json
{
  "type": "HDPE",
  "type_conf": 0.91,
  "grade": "A",
  "grade_conf": 0.88,
  "volume_cm3": 142.3,
  "dimensions": {...}
}
```

---

## ⚡ Key Innovations
* Multi-model hybrid pipeline (CNN + CLIP + Depth + YOLO)
* SAM-based training for real-world robustness
* Explicit domain shift analysis
* Zero-shot grading (no extra data required)
* Depth-based volumetric estimation

---

## 🛠️ Tech Stack

| Layer           | Technology            |
| --------------- | --------------------- |
| ML              | PyTorch, EfficientNet |
| Detection       | YOLOv8                |
| Vision-Language | CLIP                  |
| Depth           | Depth Anything V2     |
| Backend         | FastAPI               |
| Frontend        | React, TypeScript     |

---

## 🚀 Deployment
* FastAPI inference server
* YOLO detection API
* ONNX export for optimized runtime

---

## Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request
