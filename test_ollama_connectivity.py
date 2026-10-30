#!/usr/bin/env python
"""
Standalone Ollama Connectivity and Model Readiness Verification Script.
Run this script to verify that Ollama daemon is active and qwen2.5:1.5b is ready.
Usage:
    python test_ollama_connectivity.py
"""
import sys
import time

try:
    from configure import get_config
    from llm.model import check_ollama_health, query_llm
except ImportError:
    # If run outside project root
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from configure import get_config
    from llm.model import check_ollama_health, query_llm


def main():
    print("=" * 60)
    print("PronunGrammar AI - Ollama Connectivity & Verification Test")
    print("=" * 60)

    config = get_config()
    print(f"Target Ollama URL  : {config.llm.url}")
    print(f"Target Ollama Model: {config.llm.model}")
    print(f"Timeout (seconds)  : {config.llm.timeout_seconds}")
    print("-" * 60)

    print("Step 1: Pinging Ollama service...")
    health = check_ollama_health()

    if not health.get("available"):
        print(f"[FAILED] Ollama service unreachable at {health.get('url')}.")
        print(f"Error: {health.get('error')}")
        print("\nTroubleshooting tips:")
        print("  1. Ensure Ollama is installed (https://ollama.ai).")
        print("  2. In your terminal, run: ollama serve")
        print(f"  3. Pull the required model: ollama pull {config.llm.model}")
        sys.exit(1)

    print("[SUCCESS] Ollama daemon is reachable!")
    models = health.get("models", [])
    print(f"Available local models: {', '.join(models) if models else 'None'}")

    model_ready = health.get("model_installed")
    if not model_ready:
        print(f"[WARNING] Model '{config.llm.model}' was not found in installed models list.")
        print(f"Please run: ollama pull {config.llm.model}")
        print("Testing inference anyway in case of tag aliases...")

    print("-" * 60)
    print("Step 2: Sending test prompt to Ollama...")
    test_prompt = "Say 'Hello from Ollama Qwen2.5!' in 5 words or fewer."
    start_t = time.time()

    try:
        response = query_llm(test_prompt, temperature=0.1)
        duration = round(time.time() - start_t, 2)
        print(f"[SUCCESS] Ollama responded in {duration} seconds:")
        print(f"Response: {response}")
        print("=" * 60)
        print("Everything is properly configured and operational!")
        print("=" * 60)
    except Exception as exc:
        print(f"[FAILED] Inference failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
