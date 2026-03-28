import axios from "axios";

const API = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

// ── Score ──────────────────────────────────────────────────────────────────────
export const searchDevices = (q: string) =>
  API.get(`/api/score/search?q=${q}`).then(r => r.data);

export const getScore = (deviceId: string) =>
  API.get(`/api/score/${deviceId}`).then(r => r.data);

// ── Parts ──────────────────────────────────────────────────────────────────────
export const getParts = (deviceId: string) =>
  API.get(`/api/parts/${deviceId}`).then(r => r.data);

// ── RAG ───────────────────────────────────────────────────────────────────────
export const uploadManual = (sessionId: string, file: File) => {
  const form = new FormData();
  form.append("file", file);
  return API.post(`/api/rag/upload/${sessionId}`, form).then(r => r.data);
};

export const askRag = (sessionId: string, question: string, deviceName: string) =>
  API.post("/api/rag/chat", { session_id: sessionId, question, device_name: deviceName })
    .then(r => r.data);
