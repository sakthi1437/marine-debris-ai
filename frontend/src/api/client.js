import axios from "axios";
export const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000" });
export const analyze = (file, metadata, demo) => { const body = new FormData(); body.append("file", file); body.append("metadata", JSON.stringify(metadata)); return api.post(demo ? "/api/demo/run" : "/api/analyze", body); };

export function getApiError(error) {
	if (!error.response) return "Backend unavailable. Start FastAPI with: uvicorn backend.main:app --reload";
	const detail = error.response.data?.detail;
	if (typeof detail === "object" && detail?.code) return `${detail.code}: ${detail.message}`;
	return typeof detail === "string" ? detail : `Backend request failed (HTTP ${error.response.status}).`;
}
