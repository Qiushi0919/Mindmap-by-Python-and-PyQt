#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""LLM provider integration used by MindMap's AI generation feature.

The implementation intentionally uses Python's standard library instead of a
provider SDK.  This keeps OrcaRouter optional and avoids adding a runtime
dependency for users who only need the local editor.
"""

import json
import re
import socket
from urllib import error, request


ORCAROUTER_BASE_URL = "https://api.orcarouter.ai/v1"
DEFAULT_MODEL = "orcarouter/free"
DEFAULT_TIMEOUT = 90
MAX_GENERATED_NODES = 80


class ProviderError(Exception):
    """A user-facing provider or response error."""

    def __init__(self, message, status_code=None, retry_after=None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


def _error_message(payload, fallback):
    if not isinstance(payload, dict):
        return fallback
    detail = payload.get("error", payload)
    if isinstance(detail, dict):
        return detail.get("message") or detail.get("code") or fallback
    if isinstance(detail, str):
        return detail
    return fallback


def normalize_markdown(content):
    """Validate and normalize an LLM response into supported headings."""
    if not isinstance(content, str) or not content.strip():
        raise ProviderError("The model returned an empty response.")

    text = content.strip()
    fenced = re.match(r"^```(?:markdown|md)?\s*(.*?)\s*```$", text, re.I | re.S)
    if fenced:
        text = fenced.group(1).strip()

    headings = []
    for raw_line in text.splitlines():
        match = re.match(r"^\s*(#{1,3})\s+(.+?)\s*$", raw_line)
        if not match:
            continue
        level = len(match.group(1))
        title = re.sub(r"\s+#+\s*$", "", match.group(2)).strip()
        if title:
            headings.append((level, title[:120]))

    if not headings:
        raise ProviderError("The model response did not contain a concept-map outline.")
    if headings[0][0] != 1:
        headings.insert(0, (1, "AI Mind Map"))

    normalized = []
    root_seen = False
    previous_level = 0
    for level, title in headings:
        if level == 1:
            if root_seen:
                level = 2
            else:
                root_seen = True
        if previous_level and level > previous_level + 1:
            level = previous_level + 1
        normalized.append("{} {}".format("#" * level, title))
        previous_level = level
        if len(normalized) >= MAX_GENERATED_NODES:
            break

    if len(normalized) < 2:
        raise ProviderError("The model response needs at least one branch below the main topic.")
    return "\n".join(normalized)


class OrcaRouterClient(object):
    """Minimal OpenAI-compatible client for OrcaRouter."""

    def __init__(self, api_key, base_url=ORCAROUTER_BASE_URL, timeout=DEFAULT_TIMEOUT):
        api_key = (api_key or "").strip()
        if not api_key:
            raise ProviderError("Enter an OrcaRouter API key first.")
        self.api_key = api_key
        self.base_url = (base_url or ORCAROUTER_BASE_URL).rstrip("/")
        self.timeout = timeout

    def generate_mindmap(self, topic, requirements="", language="Chinese", model=DEFAULT_MODEL):
        topic = (topic or "").strip()
        model = (model or DEFAULT_MODEL).strip()
        if not topic:
            raise ProviderError("Enter a topic for the concept map.")
        if not model:
            raise ProviderError("Enter an OrcaRouter model ID.")

        system_prompt = (
            "You design concise, accurate concept maps. Return only Markdown headings. "
            "Use exactly one level-1 heading for the central topic, level-2 headings for "
            "main branches, and level-3 headings for supporting concepts. Do not use code "
            "fences, bullets, paragraphs, links, or headings deeper than level 3. Keep the "
            "map between 8 and 30 nodes and make every heading short."
        )
        user_prompt = "Create a concept map about: {}\nOutput language: {}".format(topic, language)
        if requirements.strip():
            user_prompt += "\nAdditional requirements: {}".format(requirements.strip())

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.35,
        }
        body = json.dumps(payload).encode("utf-8")
        api_request = request.Request(
            self.base_url + "/chat/completions",
            data=body,
            headers={
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "MindMap-PyQt/1.0",
            },
            method="POST",
        )

        try:
            with request.urlopen(api_request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                payload = json.loads(exc.read().decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                payload = None
            message = _error_message(payload, "OrcaRouter request failed (HTTP {}).".format(exc.code))
            if exc.code == 429 and retry_after:
                message += " Try again in {} seconds.".format(retry_after)
            elif exc.code == 429:
                message += " The free model may have reached a limit; try a shorter prompt or another model."
            raise ProviderError(message, exc.code, retry_after)
        except error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            raise ProviderError("Could not connect to OrcaRouter: {}".format(reason))
        except socket.timeout:
            raise ProviderError("The OrcaRouter request timed out. Please try again.")

        try:
            data = json.loads(raw)
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            raise ProviderError("OrcaRouter returned an unexpected response format.")
        return normalize_markdown(content)
