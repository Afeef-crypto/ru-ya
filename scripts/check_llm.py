"""Smoke-test OpenRouter (OpenAI-compatible) chat completions. Does not print the API key."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


def load_env() -> dict[str, str]:
    data: dict[str, str] = {}
    for name in (".env", ".env.local", ".env.example"):
        path = Path(name)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if key and key not in data:
                data[key] = value
    return data


def main() -> int:
    env = load_env()
    base = env.get("RUYA_LLM_BASE_URL", "").rstrip("/")
    key = env.get("RUYA_LLM_API_KEY", "")
    model = env.get("RUYA_LLM_MODEL", "openai/gpt-4o-mini")
    referer = env.get("RUYA_LLM_HTTP_REFERER", "http://localhost:3000")
    title = env.get("RUYA_LLM_APP_TITLE", "Ru-ya")

    if not key:
        print("STATUS=missing_key")
        return 2
    if not base:
        print("STATUS=missing_base_url")
        return 2

    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": "Reply with exactly: ok"}],
            "max_tokens": 16,
        }
    ).encode()

    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": referer,
            "X-Title": title,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = json.loads(resp.read().decode())
        content = body["choices"][0]["message"]["content"]
        print(f"STATUS=ok model={body.get('model', model)}")
        print("REPLY=" + content.replace("\n", " ").strip())
        return 0
    except urllib.error.HTTPError as exc:
        err = exc.read().decode(errors="replace")
        print(f"STATUS=fail http={exc.code}")
        print("ERROR=" + err[:500])
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"STATUS=fail error={type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
