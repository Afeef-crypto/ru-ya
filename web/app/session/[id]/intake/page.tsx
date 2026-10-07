"use client";

import { FormEvent, use, useState } from "react";
import { useRouter } from "next/navigation";
import { saveQuestionnaire, submitDream } from "@/lib/api";
import type { Questionnaire } from "@/lib/api-types";

const DEFAULT: Questionnaire = {
  dreamer_state: "neutral",
  dream_time: "unknown",
  repetition: "once",
  waking_emotion: "confusion",
  locale_context: "",
  sensitive_flags: ["none"],
};

export default function IntakePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [form, setForm] = useState<Questionnaire>(DEFAULT);
  const [narrative, setNarrative] = useState("");
  const [unlocked, setUnlocked] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onQuestionnaire(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await saveQuestionnaire(id, {
        ...form,
        locale_context: form.locale_context || null,
      });
      setUnlocked(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  async function onDream(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const snap = await submitDream(id, narrative);
      if (snap.state === "awaiting_followups") {
        router.push(`/session/${id}/follow-ups`);
      } else if (snap.state === "refused") {
        router.push(`/session/${id}/conclusion`);
      } else {
        router.push(`/session/${id}/conclusion`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submit failed");
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>Intake</h1>
      <p className="lead">Answer the pre-dream questions before describing the dream.</p>

      <form className="panel" onSubmit={onQuestionnaire}>
        <label>Dreamer state</label>
        <select
          value={form.dreamer_state}
          onChange={(e) => setForm({ ...form, dreamer_state: e.target.value })}
        >
          {["wudu", "grief", "illness", "anxiety", "pregnancy", "neutral", "other"].map(
            (v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ),
          )}
        </select>

        <label>Time of dream</label>
        <select
          value={form.dream_time}
          onChange={(e) => setForm({ ...form, dream_time: e.target.value })}
        >
          {["last_third_night", "after_fajr", "nap", "other_night", "unknown"].map(
            (v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ),
          )}
        </select>

        <label>Repetition</label>
        <select
          value={form.repetition}
          onChange={(e) => setForm({ ...form, repetition: e.target.value })}
        >
          {["once", "recurring", "same_theme"].map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>

        <label>Waking emotion</label>
        <select
          value={form.waking_emotion}
          onChange={(e) => setForm({ ...form, waking_emotion: e.target.value })}
        >
          {["fear", "joy", "confusion", "calm", "distress", "other"].map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>

        <label>Locale / life context (optional)</label>
        <input
          type="text"
          value={form.locale_context ?? ""}
          onChange={(e) => setForm({ ...form, locale_context: e.target.value })}
        />

        <label>Sensitive flags</label>
        <select
          value={form.sensitive_flags[0] ?? "none"}
          onChange={(e) =>
            setForm({ ...form, sensitive_flags: [e.target.value] })
          }
        >
          {["none", "prophet", "death", "blood", "sexual", "distress"].map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>

        <button type="submit" disabled={busy}>
          Save questionnaire
        </button>
      </form>

      {unlocked ? (
        <form className="panel" onSubmit={onDream}>
          <label>Dream narrative</label>
          <textarea
            value={narrative}
            onChange={(e) => setNarrative(e.target.value)}
            required
            placeholder="Describe what you saw…"
          />
          <button type="submit" disabled={busy || !narrative.trim()}>
            Continue
          </button>
        </form>
      ) : (
        <p className="muted">Dream text unlocks after the questionnaire is saved.</p>
      )}

      {error ? <p className="error">{error}</p> : null}
    </main>
  );
}
