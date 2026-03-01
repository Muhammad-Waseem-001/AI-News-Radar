import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  timeout: 15000,
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
  const { data } = await api.post("/jobs/ingest");
  return data;
}

