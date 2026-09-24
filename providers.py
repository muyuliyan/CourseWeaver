from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class HttpProvider:
    config: dict

    def validate(self) -> None:
        api_key = self.config.get("api_key", "").strip()
        if not api_key or api_key == "replace-me":
            raise RuntimeError(
                "Agent is not configured. Copy config/settings.example.json to "
                "config/settings.local.json and set agent.api_key."
            )
        if not self.config.get("model", "").strip():
            raise RuntimeError("Agent is not configured: agent.model is required.")

    def post(self, path: str, payload: dict) -> dict:
        self.validate()
        api_key = self.config["api_key"].strip()
        base_url = self.config.get("base_url", "https://api.openai.com/v1").rstrip("/")
        request = urllib.request.Request(
            f"{base_url}/{path.lstrip('/')}",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        opener = (
            urllib.request.build_opener()
            if self.config.get("use_system_proxy", False)
            else urllib.request.build_opener(urllib.request.ProxyHandler({}))
        )
        try:
            with opener.open(request, timeout=self.config.get("timeout_seconds", 120)) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Agent API request failed ({exc.code}): {detail[:500]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Cannot connect to the agent API at {base_url}. Check the API address, "
                "network access, and proxy settings. Set agent.use_system_proxy to true "
                "only when this connection requires the system proxy."
            ) from exc


class OpenAIResponsesProvider(HttpProvider):
    def generate(self, instructions: str, prompt: str) -> str:
        self.validate()
        result = self.post("responses", {
            "model": self.config["model"],
            "instructions": instructions,
            "input": prompt,
            "store": self.config.get("store", False),
        })
        text = result.get("output_text") or "".join(
            block.get("text", "")
            for output in result.get("output", [])
            for block in output.get("content", [])
            if block.get("type") == "output_text"
        )
        return text or "The model returned no text."


class OpenAICompatibleChatProvider(HttpProvider):
    def generate(self, instructions: str, prompt: str) -> str:
        self.validate()
        result = self.post("chat/completions", {
            "model": self.config["model"],
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt},
            ],
        })
        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("The compatible chat endpoint returned an unexpected response.") from exc


def create_provider(config: dict):
    providers = {
        "openai_responses": OpenAIResponsesProvider,
        "openai_compatible_chat": OpenAICompatibleChatProvider,
    }
    name = config.get("provider", "openai_responses")
    try:
        return providers[name](config)
    except KeyError as exc:
        raise RuntimeError(f"Unsupported agent provider: {name}") from exc
