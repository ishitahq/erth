export interface Feature {
  id: number;
  title: string;
  description: string;
  icon: string;
  type: 'core' | 'optional';
}

export const featuresData: Feature[] = [
  {
    id: 1,
    title: "Image-Based Classification",
    description: "Upload a photo of plastic waste and get instant classification into PET, HDPE, LDPE, PP, PS, or Unknown categories.",
    icon: "📸",
    type: "core"
  },
  {
    id: 2,
    title: "Multi-Class Prediction",
    description: "Simultaneously predicts across all 6 plastic categories with per-class probability distribution.",
    icon: "🎯",
    type: "core"
  },
  {
    id: 3,
    title: "Real-World Robustness",
    description: "Handles dirty, deformed, crushed, and mixed plastic waste under varied lighting conditions.",
    icon: "💪",
    type: "core"
  },
  {
    id: 4,
    title: "High Accuracy Metrics",
    description: "Evaluated with precision, recall, F1-score, and confusion matrix per plastic category.",
    icon: "📊",
    type: "core"
  },
  {
    id: 5,
    title: "Confidence Scoring",
    description: "Each prediction includes a confidence percentage. Low-confidence items are flagged for manual review.",
    icon: "🔍",
    type: "optional"
  },
  {
    id: 6,
    title: "Hierarchical Classification",
    description: "Optional Type → Grade classification for advanced sorting (e.g., food-grade PET vs. non-food-grade).",
    icon: "🏗️",
    type: "optional"
  },
  {
    id: 7,
    title: "Edge Deployment Ready",
    description: "Lightweight model optimized with pruning and quantization for real-time inference on embedded devices.",
    icon: "⚡",
    type: "optional"
  },
  {
    id: 8,
    title: "Volume Estimation",
    description: "Estimate plastic waste volume from images using depth estimation for throughput planning.",
    icon: "📐",
    type: "optional"
  }
];
