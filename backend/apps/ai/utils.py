import requests
import json
import logging

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
                "format": "json",  
                "options": {
                    "temperature": 0.2,
                    "num_predict": 1024,
                    "top_p": 0.9,
                },
            },
            timeout=300,
        )

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
