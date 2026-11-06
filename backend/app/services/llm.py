import requests
from backend.app.config import OLLAMA_BASE_URL, OLLAMA_MODEL

def generate(prompt: str) -> str:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=180
    )
    response.raise_for_status()
    return response.json().get("response", "").strip()
