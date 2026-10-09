from __future__ import annotations

import json
import urllib.error
import urllib.request
from functools import lru_cache

from ru_ya.config import get_settings


class LLMClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        http_referer: str = "http://localhost:3000",
        app_title: str = "Ru-ya",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.http_referer = http_referer
        self.app_title = app_title

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.base_url)

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 800,
        temperature: float = 0.2,
    ) -> str:
        if not self.enabled:
            raise RuntimeError("LLM API key is not configured")
        payload = json.dumps(
            {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        ).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.http_referer,
                "X-Title": self.app_title,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(f"LLM HTTP {exc.code}: {detail[:400]}") from exc
        return body["choices"][0]["message"]["content"]


@lru_cache
def get_llm_client() -> LLMClient:
    s = get_settings()
    return LLMClient(
        base_url=s.ruya_llm_base_url,
        api_key=s.ruya_llm_api_key,
        model=s.ruya_llm_model,
        http_referer=s.ruya_llm_http_referer,
        app_title=s.ruya_llm_app_title,
    )
