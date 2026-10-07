"use client";

import { FormEvent, useState } from "react";
import { API_BASE } from "@/lib/api-types";

export default function SourcesPage() {
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onUpload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setStatus(null);
    const form = e.currentTarget;
    const data = new FormData(form);
    try {
      const res = await fetch(`${API_BASE}/user-sources`, {
        method: "POST",
        body: data,
      });
      if (!res.ok) throw new Error(await res.text());
      const json = await res.json();
      setStatus(`Uploaded: ${json.filename} (${json.status}, ${json.chunk_count} chunks)`);
      form.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    }
  }

  return (
    <main>
      <h1>Private sources</h1>
      <p className="lead">
        TXT uploads stay scoped to your user id and never enter the curated index.
        They are labeled user-provided and cannot outrank tier-1 taxonomy hadith.
      </p>
      <form className="panel" onSubmit={onUpload}>
        <label>Owner user id</label>
        <input type="text" name="owner_user_id" defaultValue="anonymous" />
        <label>Authority preference</label>
        <select name="authority_preference" defaultValue="informational">
          <option value="informational">informational</option>
          <option value="preferred_overlay">preferred_overlay</option>
        </select>
        <label>File (.txt)</label>
        <input type="file" name="file" accept=".txt,text/plain" required />
        <button type="submit">Upload</button>
      </form>
      {status ? <p className="muted">{status}</p> : null}
      {error ? <p className="error">{error}</p> : null}
      <p>
        <a href="/">← Back</a>
      </p>
    </main>
  );
}
