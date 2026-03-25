export interface Deliverable {
  id: number;
  title: string;
  description: string;
  icon: string;
}

export const deliverablesData: Deliverable[] = [
  {
    id: 1,
    title: "Trained ML Model",
    description: "A production-ready CNN model capable of classifying 6 plastic types from images with >90% accuracy.",
    icon: "🧠"
  },
  {
    id: 2,
    title: "Dataset Documentation",
    description: "Complete dataset description including sources, preprocessing steps, augmentation techniques, and train/test splits.",
    icon: "📋"
  },
  {
    id: 3,
    title: "Performance Evaluation",
    description: "Comprehensive metrics: accuracy, per-class precision & recall, F1-scores, and confusion matrix analysis.",
    icon: "📈"
  },
  {
    id: 4,
    title: "Web Application",
    description: "Interactive web demo where users can upload plastic waste images and receive instant AI classification.",
    icon: "🌐"
  },
  {
    id: 5,
    title: "REST API",
    description: "Production API endpoint for integration with recycling facility systems and automation pipelines.",
    icon: "🔌"
  },
  {
    id: 6,
    title: "Jupyter Notebook",
    description: "Documented notebook with full training pipeline, EDA, model architecture, and evaluation visualizations.",
    icon: "📓"
  }
];
