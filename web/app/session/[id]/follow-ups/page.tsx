"use client";

import { FormEvent, use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { answerFollowUps, getSession } from "@/lib/api";
import type { FollowUpQuestion, SessionSnapshot } from "@/lib/api-types";

export default function FollowUpsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [session, setSession] = useState<SessionSnapshot | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getSession(id)
      .then((snap) => {
        setSession(snap);
        if (snap.state === "ready_to_conclude" || snap.state === "concluded") {
          router.replace(`/session/${id}/conclusion`);
        }
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Load failed"));
  }, [id, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!session) return;
    setBusy(true);
    setError(null);
    try {
      const snap = await answerFollowUps(id, answers);
      setSession(snap);
      if (snap.state === "awaiting_followups") {
        setAnswers({});
      } else {
        router.push(`/session/${id}/conclusion`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submit failed");
    } finally {
      setBusy(false);
    }
  }

  const questions: FollowUpQuestion[] = session?.pending_follow_ups ?? [];

  return (
    <main>
      <h1>Follow-up</h1>
      <p className="lead">
        Round {(session?.follow_up_round ?? 0) + 1} of{" "}
        {session?.max_follow_up_rounds ?? 3}. Answer only what is asked.
      </p>
      <form className="panel" onSubmit={onSubmit}>
        {questions.map((q) => (
          <div key={q.slot}>
            <label>{session?.language === "ar" ? q.prompt_ar : q.prompt_en}</label>
            <input
              type="text"
              value={answers[q.slot] ?? ""}
              onChange={(e) =>
                setAnswers({ ...answers, [q.slot]: e.target.value })
              }
              required
            />
          </div>
        ))}
        {!questions.length ? (
          <p className="muted">No pending questions. Continue to conclusion.</p>
        ) : null}
        <button type="submit" disabled={busy}>
          {busy ? "Saving…" : "Submit answers"}
        </button>
      </form>
      {error ? <p className="error">{error}</p> : null}
    </main>
  );
}
