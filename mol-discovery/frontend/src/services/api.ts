const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Candidate {
  id: string;
  name: string;
  type: 'known' | 'novel';
  predicted_activity: number;
  predicted_selectivity: number;
  predicted_stability: number;
  uncertainty: number;
  score: number;
  details?: string;
  novelty_score?: number;
}

export interface DiscoveryResponse {
  run_id: string;
  status: string;
  total_candidates: number;
  known_count: number;
  novel_count: number;
  candidates: Candidate[];
}

export interface ModelHealth {
  overall_accuracy: number;
  total_discrepancies: number;
  average_error: number;
  max_error: number;
  experiment_count: number;
  family_performance: Record<string, number>;
  retraining_ready: boolean;
  pending_experiments: number;
  // New fields from updated feedback service
  retraining_in_progress?: boolean;
  model_version?: string;
  val_mae?: number | null;
  val_r2?: number | null;
  last_retraining?: string | null;
}

export interface ExperimentLogResult {
  status: string;
  experiment_id?: string;
  experiments_logged?: number;
  discrepancy?: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------

export const api = {
  // ── Discovery ────────────────────────────────────────────────────────────

  startDiscovery: async (
    reaction: string,
    constraints?: Record<string, unknown>,
    userId = 'demo_user',
  ): Promise<DiscoveryResponse> => {
    const res = await fetch(`${API_BASE_URL}/api/discovery/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reaction, constraints, user_id: userId }),
    });
    return handleResponse<DiscoveryResponse>(res);
  },

  getResults: async (runId: string): Promise<DiscoveryResponse> => {
    const res = await fetch(`${API_BASE_URL}/api/discovery/${runId}/results`);
    return handleResponse<DiscoveryResponse>(res);
  },

  getStatus: async (runId: string): Promise<{ run_id: string; status: string }> => {
    const res = await fetch(`${API_BASE_URL}/api/discovery/${runId}/status`);
    return handleResponse(res);
  },

  // ── Experiment logging ────────────────────────────────────────────────────

  /** Log a single experiment via form fields */
  logExperiment: async (data: {
    candidate_id: string;
    activity: number;
    selectivity?: number;
    stability?: number;
    temperature?: number;
    pressure?: number;
    researcher?: string;
  }): Promise<ExperimentLogResult> => {
    const form = new FormData();
    Object.entries(data).forEach(([k, v]) => {
      if (v !== undefined && v !== null) form.append(k, String(v));
    });
    const res = await fetch(`${API_BASE_URL}/api/experiment/log`, {
      method: 'POST',
      body: form,
    });
    return handleResponse<ExperimentLogResult>(res);
  },

  /** Bulk-upload experiments from a CSV file */
  logExperimentCSV: async (file: File): Promise<ExperimentLogResult> => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${API_BASE_URL}/api/experiment/log`, {
      method: 'POST',
      body: form,
    });
    return handleResponse<ExperimentLogResult>(res);
  },

  // ── Model health & retraining ─────────────────────────────────────────────

  getModelHealth: async (): Promise<ModelHealth> => {
    const res = await fetch(`${API_BASE_URL}/api/model/health`);
    return handleResponse<ModelHealth>(res);
  },

  triggerRetraining: async (): Promise<{ status: string; samples_used?: number; new_model_version?: string }> => {
    const res = await fetch(`${API_BASE_URL}/api/model/retrain`, { method: 'POST' });
    return handleResponse(res);
  },

  // ── Catalyst search ───────────────────────────────────────────────────────

  searchCatalysts: async (
    query: string,
    limit = 20,
  ): Promise<{ results: Candidate[]; count: number }> => {
    const res = await fetch(
      `${API_BASE_URL}/api/catalysts/search?query=${encodeURIComponent(query)}&limit=${limit}`,
    );
    return handleResponse(res);
  },
};
