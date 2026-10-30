"""
Ollama API Integration Module for Local LLM Inference (Qwen2.5:1.5b).
Provides query_llm interface with timeouts, logging, and error handling.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    requests = None

from configure import get_config
from llm.exceptions import (
    ModelResponseError,
    OllamaConnectionError,
    OllamaTimeoutError,
)

logger = logging.getLogger("pronunciation_assessment.llm")

# Default settings retrieved dynamically from centralized configuration
_cfg = get_config()
OLLAMA_URL = _cfg.llm.url
OLLAMA_MODEL = _cfg.llm.model
OLLAMA_TIMEOUT = _cfg.llm.timeout_seconds


def check_ollama_health(url: Optional[str] = None) -> Dict[str, Any]:
    """
    Check if the Ollama daemon is reachable and responding.
    Returns status dict with connectivity and model availability.
    """
    config = get_config()
    target_url = url or config.llm.url
    if "/api/" in target_url:
        tags_url = f"{target_url.split('/api/', 1)[0]}/api/tags"
    else:
        tags_url = f"{target_url.rstrip('/')}/api/tags"

    if requests is None:
        return {
            "available": False,
            "error": "Python 'requests' package not installed. Run: pip install -r requirements.txt",
            "url": target_url,
        }

    try:
        response = requests.get(tags_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [m.get("name") for m in data.get("models", [])]
            return {
                "available": True,
                "url": tags_url,
                "models": models,
                "target_model": config.llm.model,
                "model_installed": any(config.llm.model in m for m in models),
            }
        return {
            "available": False,
            "error": f"Ollama returned HTTP status {response.status_code}",
            "url": tags_url,
        }
    except requests.exceptions.ConnectionError:
        return {
            "available": False,
            "error": f"Cannot connect to Ollama at {tags_url}. Ensure 'ollama serve' is running.",
            "url": tags_url,
        }
    except Exception as exc:
        logger.error("Unexpected Ollama health-check failure: %s", exc, exc_info=True)
        return {
            "available": False,
            "error": "Ollama health check failed unexpectedly.",
            "url": tags_url,
        }


def query_llm(
    prompt: str,
    system: Optional[str] = None,
    temperature: Optional[float] = None,
    model: Optional[str] = None,
    url: Optional[str] = None,
    timeout: Optional[int] = None,
) -> str:
    """
    Send prompt to local Ollama instance and return raw response text.

    Args:
        prompt: The input prompt for the language model.
        system: Optional system instruction prompt.
        temperature: Sampling temperature (default 0.2 for deterministic output).
        model: Target model name (default from config, e.g. qwen2.5:1.5b).
        url: Target Ollama endpoint.
        timeout: Request timeout in seconds.

    Returns:
        Generated text response from the model.

    Raises:
        OllamaConnectionError: If Ollama daemon is unreachable.
        OllamaTimeoutError: If the request exceeds the configured timeout.
        ModelResponseError: If response is empty or malformed.
    """
    config = get_config()
    if requests is None:
        raise OllamaConnectionError(
            "Python 'requests' package not installed. Run: pip install -r requirements.txt"
        )

    target_url = url or config.llm.url
    target_model = model or config.llm.model
    target_timeout = timeout if timeout is not None else config.llm.timeout_seconds
    target_temp = temperature if temperature is not None else config.llm.temperature

    payload: Dict[str, Any] = {
        "model": target_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": target_temp,
        },
    }

    if system:
        payload["system"] = system

    logger.debug(
        "Dispatching query to Ollama at %s (model: %s, timeout: %ds)",
        target_url,
        target_model,
        target_timeout,
    )

    try:
        response = requests.post(
            target_url,
            json=payload,
            timeout=target_timeout,
            headers={"Content-Type": "application/json"},
        )
    except requests.exceptions.ConnectTimeout as exc:
        logger.error("Ollama connection timed out: %s", exc)
        raise OllamaTimeoutError(
            f"Ollama connection timed out after {target_timeout} seconds at {target_url}"
        ) from exc
    except requests.exceptions.ReadTimeout as exc:
        logger.error("Ollama read response timed out: %s", exc)
        raise OllamaTimeoutError(
            f"Ollama took longer than {target_timeout}s to generate a response."
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        logger.error("Unable to connect to Ollama: %s", exc)
        raise OllamaConnectionError(
            f"Failed to connect to Ollama at {target_url}. Is Ollama running? Run 'ollama serve' and 'ollama pull {target_model}'."
        ) from exc
    except requests.exceptions.RequestException as exc:
        logger.error("Ollama request failed: %s", exc)
        raise OllamaConnectionError(f"HTTP request to Ollama failed: {exc}") from exc

    if response.status_code != 200:
        logger.error("Ollama returned status %d: %s", response.status_code, response.text)
        raise ModelResponseError(
            f"Ollama returned HTTP {response.status_code}: {response.text[:200]}"
        )

    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        logger.error("Ollama response was not valid JSON: %s", exc)
        raise ModelResponseError("Received non-JSON response from Ollama API.") from exc

    response_text = data.get("response", "").strip()
    if not response_text:
        logger.warning("Ollama returned an empty response.")
        raise ModelResponseError("Ollama returned an empty response string.")

    return response_text
