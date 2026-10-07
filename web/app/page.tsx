"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createSession } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [lang, setLang] = useState<"ar" | "en">("en");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    setBusy(true);
    setError(null);
    try {
      const session = await createSession(lang);
      router.push(`/session/${session.id}/intake`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start session");
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>Ru-ya</h1>
      <p className="lead">
        Structured intake, sourced retrieval, and cited scholarly possibilities —
        not predictions. Dreams are discarded by default after 24 hours.
      </p>
      <div className="panel">
        <label htmlFor="lang">Interface / output language</label>
        <select
          id="lang"
          value={lang}
          onChange={(e) => setLang(e.target.value as "ar" | "en")}
        >
          <option value="en">English</option>
          <option value="ar">العربية</option>
        </select>
        <div className="row">
          <button type="button" onClick={start} disabled={busy}>
            {busy ? "Starting…" : "Begin intake"}
          </button>
          <a className="button" href="/sources" style={{ background: "transparent", color: "var(--accent)", border: "1px solid var(--border)" }}>
            Private sources
          </a>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </div>
    </main>
  );
}
