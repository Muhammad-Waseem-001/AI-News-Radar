import axios from "axios";

const API_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS || 30000);
const INGEST_TIMEOUT_MS = Number(import.meta.env.VITE_INGEST_TIMEOUT_MS || 180000);
const MANUAL_INGEST_MAX_PER_FEED = Number(import.meta.env.VITE_MANUAL_INGEST_MAX_PER_FEED || 8);

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  timeout: Number.isFinite(API_TIMEOUT_MS) ? API_TIMEOUT_MS : 30000,
});

function cleanParams(params) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== "")
  );
}

export async function fetchStats() {
  const { data } = await api.get("/stats");
  return data;
}

export async function fetchArticles({ limit = 100, sentiment, category, source } = {}) {
  const params = cleanParams({ limit, sentiment, category, source });
  const { data } = await api.get("/articles", { params });
  return data;
}

export async function runIngestion() {
  const timeout = Number.isFinite(INGEST_TIMEOUT_MS) ? INGEST_TIMEOUT_MS : 180000;
  const params = Number.isFinite(MANUAL_INGEST_MAX_PER_FEED)
    ? { max_per_feed: MANUAL_INGEST_MAX_PER_FEED }
    : undefined;
  const { data } = await api.post("/jobs/ingest", null, { timeout, params });
  return data;
}
