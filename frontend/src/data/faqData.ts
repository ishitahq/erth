export interface FAQItem {
  id: number;
  question: string;
  answer: string;
}

export const faqData: FAQItem[] = [
  {
    id: 1,
    question: "What is the ROI of deploying Erth in our facility?",
    answer: "Facilities typically see a 25–40% improvement in sorting accuracy within the first quarter. This translates to higher-quality recyclate output, reduced contamination penalties, lower manual labor costs, and increased revenue from properly sorted materials. Most clients achieve full ROI within 6–12 months."
  },
  {
    id: 2,
    question: "How does Erth integrate with our existing sorting infrastructure?",
    answer: "Erth is designed to be retrofit-friendly. It connects to existing conveyor systems via standard industrial camera mounts and communicates with PLCs through common protocols (Modbus, OPC-UA). Our deployment team handles calibration, integration testing, and staff training with minimal disruption to your operations."
  },
  {
    id: 3,
    question: "What throughput can the system handle?",
    answer: "Erth processes images in real-time at conveyor speeds up to 3 m/s. A single camera unit can classify up to 60 items per minute. For higher-volume lines, multiple camera units can be deployed in parallel with a centralized dashboard for monitoring and analytics."
  },
  {
    id: 4,
    question: "How accurate is the classification, and how do you handle misclassification?",
    answer: "Our model achieves over 92% accuracy across all six plastic categories (PET, HDPE, LDPE, PP, PS, and Other). Every prediction includes a confidence score — items below the configurable threshold are flagged for manual review, ensuring contamination rates stay well below industry benchmarks."
  },
  {
    id: 5,
    question: "Does the system work with dirty, crushed, or mixed plastic waste?",
    answer: "Yes. The model is trained on real-world waste images including items that are dirty, deformed, partially labeled, and mixed. Advanced data augmentation during training ensures robust performance across the full range of conditions found in MRFs and recycling plants."
  },
  {
    id: 6,
    question: "What kind of maintenance and support is included?",
    answer: "Erth includes over-the-air model updates, 24/7 remote monitoring, and quarterly performance reviews. Our support team provides on-site maintenance for camera hardware and continuous model retraining on your facility's specific waste stream to improve accuracy over time."
  },
  {
    id: 7,
    question: "Can Erth generate compliance reports and analytics?",
    answer: "Absolutely. The management dashboard provides real-time sorting metrics, contamination rate tracking, throughput analytics, and exportable reports aligned with EPR regulations and ISO standards. Custom reporting for audits and sustainability disclosures is also available."
  },
  {
    id: 8,
    question: "What is the deployment timeline from purchase to production?",
    answer: "A standard deployment takes 4–6 weeks: site assessment (1 week), hardware installation and integration (2 weeks), model calibration on your waste stream (1 week), and staff training plus go-live support (1–2 weeks). Expedited deployment is available for urgent requirements."
  },
  {
    id: 9,
    question: "Is Erth scalable across multiple facility locations?",
    answer: "Yes. Erth supports multi-site deployment with a unified cloud dashboard for centralized monitoring. Each facility's model can be independently fine-tuned for local waste stream characteristics while sharing aggregate analytics and best practices across your entire operation."
  }
];
