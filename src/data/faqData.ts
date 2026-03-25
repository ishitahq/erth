export interface FAQItem {
  id: number;
  question: string;
  answer: string;
}

export const faqData: FAQItem[] = [
  {
    id: 1,
    question: "What types of plastic can the system classify?",
    answer: "The system classifies plastics into six categories: PET (Polyethylene Terephthalate), HDPE (High-Density Polyethylene), LDPE (Low-Density Polyethylene), PP (Polypropylene), PS (Polystyrene), and Other/Unknown plastics. These cover virtually all consumer plastic waste."
  },
  {
    id: 2,
    question: "How does the AI classify plastic from images?",
    answer: "The system uses a Convolutional Neural Network (CNN) trained on thousands of labeled plastic waste images. It analyzes visual features like texture, transparency, shape, and surface patterns to predict the plastic type. Transfer learning from models like ResNet or EfficientNet is used to boost accuracy."
  },
  {
    id: 3,
    question: "Can it handle dirty or deformed plastic?",
    answer: "Yes. The model is trained with extensive data augmentation including random rotations, lighting variations, noise injection, and simulated dirt/damage. This ensures robust performance on real-world waste that may be crushed, dirty, or partially obscured."
  },
  {
    id: 4,
    question: "What accuracy does the model achieve?",
    answer: "The model targets over 90% accuracy across all plastic categories. Per-class precision and recall are tracked to identify and minimize misclassification between visually similar categories like PET and PS, or HDPE and PP."
  },
  {
    id: 5,
    question: "Why is correct plastic classification important?",
    answer: "Incorrect classification leads to contamination in recycling streams. For example, mixing PET with PVC can ruin an entire batch of recycled material. Accurate sorting improves recycled material quality, increases economic value, and reduces landfill waste."
  },
  {
    id: 6,
    question: "Can this system be deployed at the edge?",
    answer: "Yes. The system supports lightweight model variants optimized for edge deployment using techniques like model pruning, quantization, and knowledge distillation. This enables real-time classification on conveyor belts, mobile devices, or IoT sensors in recycling facilities."
  },
  {
    id: 7,
    question: "Does the system provide confidence scores?",
    answer: "Yes. Each prediction comes with a confidence score indicating how certain the model is about its classification. Low-confidence predictions can be flagged for human review, reducing the risk of contamination in recycling streams."
  },
  {
    id: 8,
    question: "What data was used to train the model?",
    answer: "The model is trained on publicly available plastic waste image datasets combined with custom-collected images. The dataset undergoes preprocessing (resizing, normalization) and augmentation (flipping, rotation, color jitter, noise) to ensure diversity and generalization."
  },
  {
    id: 9,
    question: "Can it estimate the volume of plastic waste?",
    answer: "As an optional enhancement, the system can estimate volumetric characteristics of plastic waste from images using depth estimation or reference-object scaling. This helps recycling facilities estimate throughput and plan processing capacity."
  }
];
