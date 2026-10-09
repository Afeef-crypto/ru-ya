"""End-to-end API flow against a running server (or in-process orchestrator fallback)."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

API = "http://127.0.0.1:8000/api/v1"


def http_json(method: str, path: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def read_sse_conclude(session_id: str) -> dict:
    req = urllib.request.Request(
        f"{API}/sessions/{session_id}/conclude",
        method="POST",
        headers={"Accept": "text/event-stream"},
    )
    final: dict = {}
    with urllib.request.urlopen(req, timeout=180) as resp:
        event = "message"
        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="replace").rstrip("\n")
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                payload = line[5:].strip()
                try:
                    data = json.loads(payload)
                except json.JSONDecodeError:
                    data = {"raw": payload}
                print(f"SSE {event}")
                if event in {"done", "refused"}:
                    final = data if isinstance(data, dict) else {"data": data}
    return final


def main() -> int:
    try:
        health = urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5)
        print("HEALTH", health.read().decode())
    except Exception as exc:  # noqa: BLE001
        print(f"STATUS=api_down error={exc}")
        return 2

    session = http_json("POST", "/sessions", {"language": "en", "retain": False})
    sid = session["id"]
    print("SESSION", sid, session["state"])

    session = http_json(
        "PUT",
        f"/sessions/{sid}/questionnaire",
        {
            "dreamer_state": "anxiety",
            "dream_time": "other_night",
            "repetition": "once",
            "waking_emotion": "fear",
            "locale_context": "urban apartment",
            "sensitive_flags": ["none"],
        },
    )
    print("QUESTIONNAIRE", session["state"])

    session = http_json(
        "POST",
        f"/sessions/{sid}/dream",
        {
            "narrative": (
                "I saw a snake indoors at night. A man was standing nearby. "
                "I only observed and woke afraid."
            )
        },
    )
    print("DREAM", session["state"], "followups", len(session.get("pending_follow_ups") or []))

    while session["state"] == "awaiting_followups" and session.get("pending_follow_ups"):
        answers = {}
        for q in session["pending_follow_ups"]:
            slot = q["slot"]
            answers[slot] = {
                "people_identity": "unknown man",
                "setting_indoor_outdoor": "indoors",
                "setting_day_night": "night",
                "observer_or_actor": "only observe",
            }.get(slot, "unknown")
        session = http_json("POST", f"/sessions/{sid}/follow-ups", {"answers": answers})
        print("FOLLOWUP", session["state"], "round", session.get("follow_up_round"))

    conclusion = read_sse_conclude(sid)
    print("CONCLUSION_KEYS", sorted(conclusion.keys()))
    print(
        json.dumps(
            {
                "classification": conclusion.get("classification"),
                "confidence": conclusion.get("confidence"),
                "abstained": conclusion.get("abstained"),
                "claims": len(conclusion.get("claims") or []),
                "evidence": len(conclusion.get("evidence") or []),
                "conclusion_preview": (conclusion.get("conclusion_md") or "")[:400],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print("STATUS=ok")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as exc:
        print("STATUS=fail http", exc.code, exc.read().decode(errors="replace")[:500])
        raise SystemExit(1)
