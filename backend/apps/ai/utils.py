import requests
import json
import logging
import os
import time
from functools import lru_cache

import numpy as np

logger = logging.getLogger(__name__)

# Any OpenAI-compatible chat API. The default is a local Ollama; a hosted one
# (Groq, Gemini, ...) is the same call with a different URL, key and model.
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1").rstrip("/")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "ollama")
MODEL = os.environ.get("LLM_MODEL", "qwen2.5:7b")
# CPU-only hosts generate a few tokens/s; a 2048-token batch can outlast 5 minutes.
TIMEOUT = int(os.environ.get("LLM_TIMEOUT", 300))
# Reasoning models (gpt-oss) spend max_tokens on hidden reasoning first; "low"
# leaves room for the JSON. Unset for models that reject the field (qwen2.5).
REASONING_EFFORT = os.environ.get("LLM_REASONING_EFFORT", "")


def _post(prompt):
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
        "max_tokens": 2048,  # headroom for a 20-posting skills batch
        "top_p": 0.9,
    }
    if REASONING_EFFORT:
        body["reasoning_effort"] = REASONING_EFFORT
    return requests.post(
        f"{LLM_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {LLM_API_KEY}"},
        json=body,
        timeout=TIMEOUT,
    )


def ask_model(prompt: str):
    try:
        response = _post(prompt)
        if response.status_code == 429:
            # Free hosted tiers rate-limit per minute; one wait usually clears it.
            time.sleep(min(float(response.headers.get("retry-after") or 10), 60))
            response = _post(prompt)

        if response.status_code >= 400:
            # The body holds the real cause ("model 'x' not found", "invalid key"),
            # which raise_for_status alone throws away.
            logger.error("LLM %s for model %r: %.300s", response.status_code, MODEL, response.text)
            response.raise_for_status()

        raw_text = (response.json()["choices"][0]["message"]["content"] or "").strip()

        if not raw_text:
            logger.warning("⚠️ Empty model response")
            return {}

        try:
            parsed = json.loads(raw_text)
            return parsed
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON decode error: {e}")
            logger.warning(f"RAW MODEL OUTPUT:\n{raw_text}")
            return {}

    except Exception as e:
        # None, not {}: callers must be able to tell "model unreachable" from
        # "model found nothing", or an outage reads as an empty resume.
        logger.error(f"LLM error: {e}")
        return None


# Loaded once, on first use (importing this module must not hit the network).
# fastembed runs all-MiniLM-L6-v2 on ONNX: the same 384-d normalized vectors as
# sentence-transformers, without torch, so it fits a 512 MB host.
@lru_cache(maxsize=1)
def _embedder():
    from fastembed import TextEmbedding

    return TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")


def embed(texts):
    """Unit-length 384-d vectors, one row per text."""
    return np.array(list(_embedder().embed(texts)))
