# ♻️ Erth — AI-Powered Plastic Waste Classification System

Erth is an AI/ML-based system that automatically classifies plastic waste into specific types using images — enabling smarter recycling, reducing contamination, and building a circular economy.

---

## 🌍 Problem Context

Plastic waste is one of the most critical environmental challenges due to its non-biodegradable nature and long-term ecological impact. Recycling is key to building sustainable and circular economies, but its effectiveness depends on correctly identifying plastic types.

Different plastics — **PET, HDPE, LDPE, PP, and PS** — have unique chemical properties, melting points, and recycling methods. Incorrect classification leads to:

- **Contamination** of recycling streams
- **Reduced quality** of recycled materials
- **Lower economic value** of output

Currently, plastic identification in recycling facilities is mostly **manual**, making the process slow, labor-intensive, and prone to errors — especially with dirty, mixed, or deformed plastic waste.

---

## 🎯 The Core Challenge

Develop an AI/ML-based system that can automatically classify plastic waste into specific types using images.

The system must:

- Accurately distinguish between visually similar plastic categories
- Handle real-world conditions such as dirt, deformation, and lighting variations
- Minimize misclassification to reduce contamination in recycling streams
- Generalize well across diverse datasets and environments

---

## ✨ Features

### Core Features

- **Image-based classification** of plastic waste
- **Multi-class prediction** across categories:

| Code | Plastic Type | Description |
|------|-------------|-------------|
| #1 | **PET** | Polyethylene Terephthalate |
| #2 | **HDPE** | High-Density Polyethylene |
| #3 | **LDPE** | Low-Density Polyethylene |
| #4 | **PP** | Polypropylene |
| #5 | **PS** | Polystyrene |
| #6 | **Other** | Mixed / Unknown Plastics |

- **Robust performance** on real-world waste images (dirty, deformed, mixed)

### Optional Enhancements

- 📊 **Confidence score** for each prediction
- 🏷️ **Hierarchical classification** (Type → Grade)
- ⚡ **Lightweight model** for edge deployment
- 📐 **Volumetric estimation** of plastic waste using images

---

## 📦 Expected Output

The final system delivers:

1. **Trained ML Model** — Capable of classifying plastic types from images
2. **Dataset Documentation** — Sources, preprocessing steps, and augmentation techniques
3. **Performance Evaluation** using:
   - Accuracy
   - Precision and Recall (per plastic category)
   - Confusion Matrix
4. **Working Demonstration** — Web application, REST API, or Jupyter notebook

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Animations | Framer Motion |
| ML Model | CNN with Transfer Learning (ResNet / EfficientNet) |
| Training | Data Augmentation, Fine-tuning |
| Deployment | Web App, REST API, Edge Devices |

---

## 🚀 Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) (v18+)
- npm or yarn

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/erth.git
cd erth/frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The app will be running at `http://localhost:5173`.

### Production Build

```bash
npm run build
```

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/       # UI components (HeroSection, StatisticsSection, FAQSection, etc.)
│   ├── data/             # Static data (FAQ, statistics, plastic types, etc.)
│   ├── hooks/            # Custom React hooks (scroll animations)
│   ├── utils/            # Utility functions
│   ├── assets/           # Static assets
│   ├── App.tsx           # Main application component
│   ├── index.css         # Global styles and design tokens
│   └── main.tsx          # Application entry point
├── public/               # Public assets (images, icons)
├── index.html            # HTML entry point
├── tailwind.config.js    # Tailwind CSS configuration
├── vite.config.ts        # Vite configuration
└── package.json          # Dependencies and scripts
```

---

## 📊 ML Pipeline

```
Data Collection → Preprocessing & Augmentation → Model Training → Evaluation & Optimization → Deployment
```

1. **Data Collection** — Diverse plastic waste images from public datasets and custom sources
2. **Preprocessing & Augmentation** — Resize, normalize, rotate, flip, noise, and color jitter
3. **Model Training** — CNN with transfer learning (ResNet/EfficientNet), fine-tuned on plastic waste
4. **Evaluation** — Accuracy, precision, recall, confusion matrix, and threshold optimization
5. **Deployment** — Web app, REST API, or edge device integration

---

## 📄 License

This project is developed as part of an academic / hackathon problem statement on plastic waste classification.

---

> **Erth** — *Classify. Recycle. Sustain.* ♻️
