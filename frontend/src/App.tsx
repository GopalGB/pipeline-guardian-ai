import { useEffect, useState } from "react";
import { analyze, decide, listIncidents, poll, retry } from "./api";
import type { Incident } from "./types";
import "./styles.css";

export default function App() {
  const [incidents, setIncidents] = useState<Incident[]>([]); const [actor, setActor] = useState(""); const [reason, setReason] = useState(""); const [error, setError] = useState("");
  const refresh = () => listIncidents().then(setIncidents).catch(() => setError("Unable to load incidents"));
  async function pollNow() { try { setError(""); await poll(); await refresh(); } catch { setError("Unable to poll pipeline source"); } }
  async function analyzeNow() { if (!selected) return; try { setError(""); await analyze(selected.id); await refresh(); } catch { setError("Analysis provider is unavailable"); } }
  useEffect(() => { refresh(); }, []);
  const selected = incidents[0];
  async function action(kind: "approve" | "reject") { if (!selected || !actor || !reason) return; try { await decide(selected.id, kind, actor, reason); await refresh(); } catch { setError("Decision failed"); } }
 return <main><header><p className="eyebrow">PIPELINE GUARDIAN AI</p><h1>Operator recovery desk</h1><p>Review failed pipeline work before any allowlisted retry.</p><button onClick={pollNow}>Poll source</button></header>{error && <p role="alert" className="error">{error}</p>}{!selected && !error && <p className="empty">No incidents require attention.</p>}{selected && <section aria-labelledby="incident-title"><div className="status"><span className={`badge ${selected.state}`}>{selected.state}</span><span>Incident #{selected.id}</span></div><h2 id="incident-title">Failed pipeline task</h2><div className="grid"><article><h3>Evidence</h3><pre>{JSON.stringify(selected.evidence, null, 2)}</pre></article><article><h3>Runbooks</h3><pre>{JSON.stringify(selected.retrieved_runbooks ?? [], null, 2)}</pre></article><article><h3>Analysis</h3><pre>{JSON.stringify(selected.analysis ?? { status: "analysis_failed" }, null, 2)}</pre><button onClick={analyzeNow} disabled={selected.state !== "detected"}>Analyze incident</button></article><article><h3>Audit</h3><pre>{JSON.stringify(selected.audit ?? [], null, 2)}</pre></article></div><label>Operator name<input value={actor} onChange={event => setActor(event.target.value)} /></label><label>Decision reason<textarea value={reason} onChange={event => setReason(event.target.value)} /></label><div className="actions"><button onClick={() => action("approve")} disabled={selected.state !== "awaiting_approval" || !actor || !reason}>Approve retry</button><button onClick={() => action("reject")} disabled={selected.state !== "awaiting_approval" || !actor || !reason}>Reject</button><button onClick={() => retry(selected.id)} disabled={selected.state !== "approved"}>Dispatch approved retry</button></div><p className="audit">Final state: <strong>{selected.state}</strong></p></section>}</main>;
}
