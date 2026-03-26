/**
 * API client for the Plastic Waste Classification backend.
 * Calls POST /classify on the FastAPI server.
 *
 * If the backend is unreachable, returns a structured error.
 */

const API_BASE = 'http://localhost:8000';

// ── Response types (match backend schemas.py) ────────────────────────────────

export interface GradeScores {
  A: number | null;
  B: number | null;
  C: number | null;
}

export interface Dimensions {
  width_cm: number;
  height_cm: number;
}

export interface ClassificationResult {
  // Stage 1 — Type
  plastic_type: string;
  type_confidence: number;
  all_class_scores: Record<string, number> | null;

  // Stage 2 — Grade
  grade: string | null;
  grade_confidence: number | null;
  grade_scores: GradeScores | null;
  action: string | null;

  // Stage 3 — Volume
  volume_cm3: number | null;
  dimensions: Dimensions | null;

  // Meta
  backend_used: string;
  tta_used: boolean;
}

// ── API call ─────────────────────────────────────────────────────────────────

export async function classifyImage(file: File): Promise<ClassificationResult> {
  const formData = new FormData();
  formData.append('file', file);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/classify`, {
      method: 'POST',
      body: formData,
    });
  } catch {
    throw new Error(
      'Cannot connect to the backend server. Make sure uvicorn is running:\n' +
      'cd backend && python -m uvicorn app.main:app --port 8000'
    );
  }

  if (!res.ok) {
    let detail = '';
    try { detail = await res.text(); } catch { /* ignore */ }
    throw new Error(`Classification failed (${res.status}): ${detail || 'Unknown server error'}`);
  }

  return res.json();
}

// ── Health check ─────────────────────────────────────────────────────────────

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

// ── Display helpers ──────────────────────────────────────────────────────────

export const CLASS_COLORS: Record<string, string> = {
  PET:   '#e74c3c',
  HDPE:  '#52a8db',
  LDPE:  '#f39c12',
  PP:    '#7ed957',
  PS:    '#9b59b6',
  OTHER: '#95a5a6',
  Unknown: '#6b7280',
};

export const GRADE_COLORS: Record<string, string> = {
  A: '#7ed957',
  B: '#f59e0b',
  C: '#ef4444',
};

export const GRADE_LABELS: Record<string, string> = {
  A: 'Recyclable',
  B: 'Needs Pre-Processing',
  C: 'Not Recyclable',
};

export const RECYCLING_TIPS: Record<string, string> = {
  PET:   'Most recyclable — water bottles and food containers. Rinse and remove labels when possible.',
  HDPE:  'Highly recyclable — found in milk jugs and detergent bottles. One of the easiest plastics to recycle.',
  LDPE:  'Limited recyclability — plastic bags and wraps. Check if your local facility accepts them.',
  PP:    'Recyclable — used in yogurt cups, bottle caps, and straws. Wash before recycling.',
  PS:    'Difficult to recycle — styrofoam cups and packing peanuts. Most facilities do not accept PS.',
  OTHER: 'Mixed or multi-layer plastic — check local guidelines. Often not recyclable.',
  Unknown: 'Could not identify plastic type. Manual inspection recommended.',
};
