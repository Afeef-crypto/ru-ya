"use client";

import { use, useEffect, useState } from "react";
import {
  concludeSession,
  discardSession,
  getConclusion,
  getSession,
} from "@/lib/api";
import type { ConclusionPayload, SessionSnapshot } from "@/lib/api-types";

export default function ConclusionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [session, setSession] = useState<SessionSnapshot | null>(null);
  const [conclusion, setConclusion] = useState<ConclusionPayload | null>(null);
  const [status, setStatus] = useState<string>("Loading…");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const snap = await getSession(id);
        if (cancelled) return;
        setSession(snap);
        if (snap.state === "concluded" || snap.state === "refused") {
          try {
            const c = await getConclusion(id);
            if (!cancelled) setConclusion(c);
          } catch {
            /* refused may still have payload on session path */
          }
          setStatus(snap.state);
          return;
        }
        setStatus("Retrieving & drafting…");
        const c = await concludeSession(id, (event) => {
          if (!cancelled) setStatus(event);
        });
        if (!cancelled) {
          setConclusion(c);
          setStatus("done");
          setSession(await getSession(id));
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  return (
    <main>
      <h1>Conclusion</h1>
      <p className="lead">
        Status: <span className="badge">{status}</span>
        {session ? <span className="badge">{session.state}</span> : null}
      </p>

      {conclusion ? (
        <>
          <div className="panel">
            <p>
              Classification: <strong>{conclusion.classification.label}</strong>{" "}
              · Confidence: <strong>{conclusion.confidence.score}</strong>/100
            </p>
            <pre className="md">{conclusion.conclusion_md}</pre>
            {conclusion.adab?.text ? (
              <p className="muted">{conclusion.adab.text}</p>
            ) : null}
          </div>

          <div className="panel">
            <h2 style={{ fontFamily: "var(--font-display)", marginTop: 0 }}>
              Confidence breakdown
            </h2>
            <ul className="muted">
              {Object.entries(conclusion.confidence.breakdown).map(([k, v]) => (
                <li key={k}>
                  {k}: {(v as number).toFixed(2)}
                </li>
              ))}
            </ul>
          </div>

          <div className="panel">
            <h2 style={{ fontFamily: "var(--font-display)", marginTop: 0 }}>
              Evidence
            </h2>
            {conclusion.evidence.map((ev, i) => (
              <div key={i} style={{ marginBottom: "1rem" }}>
                <span className="badge">tier {ev.reliability_tier ?? "?"}</span>
                {ev.hadith_grade ? (
                  <span className="badge">{ev.hadith_grade}</span>
                ) : null}
                <span className="badge">{ev.source_scope}</span>
                {ev.pending_scholar_review ? (
                  <span className="badge">pending review</span>
                ) : null}
                <p>{ev.excerpt}</p>
                <p className="muted">
                  {ev.author} · {ev.cite_key ?? ev.citation_id}
                </p>
              </div>
            ))}
          </div>

          {conclusion.gaps?.length ? (
            <div className="panel">
              <h2 style={{ fontFamily: "var(--font-display)", marginTop: 0 }}>
                Gaps
              </h2>
              <p className="muted">{conclusion.gaps.join(", ")}</p>
            </div>
          ) : null}
        </>
      ) : null}

      <div className="row">
        <button
          type="button"
          onClick={async () => {
            await discardSession(id);
            window.location.href = "/";
          }}
        >
          Discard session
        </button>
      </div>
      {error ? <p className="error">{error}</p> : null}
    </main>
  );
}
