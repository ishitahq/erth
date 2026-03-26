export interface Deliverable {
  id: number;
  title: string;
  description: string;
  icon: string;
}

export const deliverablesData: Deliverable[] = [
  {
    id: 1,
    title: "6-Type Plastic Classification",
    description: "AI identifies PET, HDPE, LDPE, PP, PS, and PVC — each with distinct recycling pathways and melting points for accurate sorting.",
    icon: "🔬"
  },
  {
    id: 2,
    title: "Confidence Score",
    description: "Every detection comes with a per-class confidence percentage, enabling operators to set custom acceptance thresholds.",
    icon: "🎯"
  },
  {
    id: 3,
    title: "Per-Type Instance Count",
    description: "Real-time tally of each plastic type detected in a single image — critical for batch composition analysis.",
    icon: "📊"
  },
  {
    id: 4,
    title: "Annotated Bounding Box Output",
    description: "Returns the original image with color-coded bounding boxes drawn around each detected plastic piece for visual verification.",
    icon: "🖼️"
  },
  {
    id: 5,
    title: "Volumetric Estimation",
    description: "Approximates the volume-to-weight ratio of detected plastics using bounding box dimensions, aiding logistics and throughput planning.",
    icon: "📐"
  },
  {
    id: 6,
    title: "Recyclability Grade Prediction",
    description: "Assigns each plastic a recyclability grade (A–D) based on type, contamination likelihood, and regional recycling infrastructure compatibility.",
    icon: "♻️"
  }
];
