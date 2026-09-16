import requests
import json
import logging
import os

logger = logging.getLogger(__name__)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")


def ask_model(prompt: str):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",  
                "options": {
                    "temperature": 0.2,
                    "num_predict": 2048,  # headroom for a 20-posting skills batch
                    "top_p": 0.9,
                },
            },
            timeout=300,
        )

        if response.status_code >= 400:
            # Ollama puts the real cause here ("model 'x' not found, try pulling it"),
            # which raise_for_status alone throws away.
            logger.error("Ollama %s for model %r: %.300s", response.status_code, MODEL, response.text)
            response.raise_for_status()

        raw_text = response.json().get("response", "").strip()

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
        logger.error(f"Ollama error: {e}")
        return {}
