import {
  API_BASE,
  ConclusionPayload,
  Questionnaire,
  SessionSnapshot,
} from "./api-types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || res.statusText);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export function createSession(language: "ar" | "en" = "en") {
  return request<SessionSnapshot>("/sessions", {
    method: "POST",
    body: JSON.stringify({ language, retain: false }),
  });
}

export function saveQuestionnaire(id: string, body: Questionnaire) {
  return request<SessionSnapshot>(`/sessions/${id}/questionnaire`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export function submitDream(id: string, narrative: string) {
  return request<SessionSnapshot>(`/sessions/${id}/dream`, {
    method: "POST",
    body: JSON.stringify({ narrative }),
  });
}

export function answerFollowUps(id: string, answers: Record<string, string>) {
  return request<SessionSnapshot>(`/sessions/${id}/follow-ups`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  });
}

export function getSession(id: string) {
  return request<SessionSnapshot>(`/sessions/${id}`);
}

export function getConclusion(id: string) {
  return request<ConclusionPayload>(`/sessions/${id}/conclusion`);
}

export function discardSession(id: string) {
  return request<void>(`/sessions/${id}`, { method: "DELETE" });
}

/** Consume SSE conclude stream; resolves when `done` or `refused` fires. */
export async function concludeSession(
  id: string,
  onEvent?: (event: string, data: unknown) => void,
): Promise<ConclusionPayload | null> {
  const res = await fetch(`${API_BASE}/sessions/${id}/conclude`, {
    method: "POST",
  });
  if (!res.ok || !res.body) {
    throw new Error("conclude failed");
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let final: ConclusionPayload | null = null;
  let currentEvent = "message";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n");
    buffer = parts.pop() ?? "";
    for (const line of parts) {
      if (line.startsWith("event:")) {
        currentEvent = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        const raw = line.slice(5).trim();
        let data: unknown = raw;
        try {
          data = JSON.parse(raw);
        } catch {
          /* keep string */
        }
        onEvent?.(currentEvent, data);
        if (currentEvent === "done" || currentEvent === "refused") {
          final = data as ConclusionPayload;
        }
      }
    }
  }
  return final;
}
