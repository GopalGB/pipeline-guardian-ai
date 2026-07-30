import type { Incident } from "./types";
export async function listIncidents(): Promise<Incident[]> { const response = await fetch("/api/incidents"); if (!response.ok) throw new Error("API error"); return response.json(); }
export async function poll(): Promise<void> { const response = await fetch("/api/poll", { method: "POST" }); if (!response.ok) throw new Error("Poll failed"); }
export async function analyze(id: number): Promise<void> { const response = await fetch(`/api/incidents/${id}/analyze`, { method: "POST" }); if (!response.ok) throw new Error("Analysis failed"); }
export async function decide(id: number, action: "approve" | "reject", actor: string, reason: string): Promise<void> { const response = await fetch(`/api/incidents/${id}/${action}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ actor, reason }) }); if (!response.ok) throw new Error("Decision failed"); }
export async function retry(id: number): Promise<void> { const response = await fetch(`/api/incidents/${id}/retry`, { method: "POST" }); if (!response.ok) throw new Error("Retry failed"); }
