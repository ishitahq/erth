/**
 * Mock inference utility — simulates YOLOv8 plastic detection results.
 * Replace the `mockClassify` function body with a real `fetch()` call
 * once the backend API is deployed.
 */

export interface Detection {
  classId: number;
  className: string;
  confidence: number;
  bbox: { x: number; y: number; w: number; h: number }; // normalized 0-1
  color: string;
}

export interface InferenceResult {
  detections: Detection[];
  inferenceTimeMs: number;
}

const CLASS_INFO: Record<number, { name: string; color: string }> = {
  0: { name: 'PP', color: '#7ed957' },
  1: { name: 'HDPE', color: '#52a8db' },
  2: { name: 'PET', color: '#e74c3c' },
  3: { name: 'Rigid', color: '#9b59b6' },
};

function randomBetween(min: number, max: number): number {
  return Math.random() * (max - min) + min;
}

function generateMockDetections(): Detection[] {
  const count = Math.floor(randomBetween(2, 6));
  const detections: Detection[] = [];

  for (let i = 0; i < count; i++) {
    const classId = Math.floor(Math.random() * 4);
    const info = CLASS_INFO[classId];

    // Generate non-overlapping bounding boxes spread across the image
    const bw = randomBetween(0.12, 0.30);
    const bh = randomBetween(0.12, 0.30);
    const bx = randomBetween(0.05, 0.95 - bw);
    const by = randomBetween(0.05, 0.95 - bh);

    detections.push({
      classId,
      className: info.name,
      confidence: randomBetween(0.72, 0.99),
      bbox: { x: bx, y: by, w: bw, h: bh },
      color: info.color,
    });
  }

  return detections;
}

/**
 * Simulate model inference with a delay.
 * Replace this function body with a real API call when the backend is ready:
 *
 * ```ts
 * const formData = new FormData();
 * formData.append('file', imageFile);
 * const res = await fetch('http://localhost:8000/predict', { method: 'POST', body: formData });
 * return await res.json();
 * ```
 */
export async function mockClassify(): Promise<InferenceResult> {
  const delay = randomBetween(1500, 2500);
  await new Promise((resolve) => setTimeout(resolve, delay));

  return {
    detections: generateMockDetections(),
    inferenceTimeMs: Math.round(delay),
  };
}

export const RECYCLING_TIPS: Record<string, string> = {
  PP: 'Recyclable — used in yogurt cups, bottle caps, and straws. Wash before recycling.',
  HDPE: 'Highly recyclable — found in milk jugs and detergent bottles. One of the easiest plastics to recycle.',
  PET: 'Most recyclable — water bottles and food containers. Rinse and remove labels when possible.',
  Rigid: 'Check local guidelines — rigid plastics vary. Some facilities accept them, others don\'t.',
};
