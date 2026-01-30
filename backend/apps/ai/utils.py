import requests
import json
import logging
import re

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3:mini"


def ask_model(prompt: str):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,     # NOT zero
                    "num_predict": 1024,    # Phi-3 needs room
                    "top_p": 0.9,
                },
                # ❌ REMOVE format=json
            },
            timeout=120,
        )

        response.raise_for_status()
        text = response.json().get("response", "").strip()

        if not text:
            logger.warning("⚠️ Empty model response")
            return []

        # Extract JSON array
        match = re.search(r"\[\s*{.*}\s*\]", text, re.DOTALL)
        if not match:
            logger.warning("⚠️ No JSON array found")
            return []

        return json.loads(match.group())

    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return []
