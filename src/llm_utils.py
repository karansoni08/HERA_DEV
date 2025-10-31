# src/llm_utils.py
from pathlib import Path
import os, json, requests
from jsonschema import validate

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "mistral")

class LLMError(RuntimeError): ...
def _raise(msg, resp=None):
    details = f" | status={getattr(resp, 'status_code', 'NA')} body={getattr(resp, 'text', '')[:400]}"
    raise LLMError(msg + details)

def call_model(prompt: str, model: str = MODEL, stream: bool = False) -> str:
    # Try /api/generate
    try:
        r = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("response", "")
        # If 404 (or other), try /api/chat next
    except requests.exceptions.ConnectionError as e:
        # server not reachable
        raise LLMError(f"Ollama server not reachable at {OLLAMA_HOST}. Did you run `ollama serve`?") from e

    # Try /api/chat (some setups prefer chat-style)
    r = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=120,
    )
    if r.status_code == 200:
        data = r.json()
        # Ollama chat returns {"message":{"role":"assistant","content":"..."}}
        msg = (data.get("message") or {}).get("content", "")
        if msg:
            return msg
        # Some variants return 'response'
        return data.get("response", "")

    if r.status_code == 404:
        _raise(
            "404 from Ollama API. Check that Ollama is running on the expected port "
            "and you’re calling the correct path (/api/generate or /api/chat).",
            r,
        )
    elif r.status_code == 500 and "no such model" in r.text.lower():
        _raise(
            f"Model '{model}' not found. Run `ollama pull {model}` first, or set OLLAMA_MODEL.",
            r,
        )
    else:
        _raise("Unexpected error from LLM endpoint.", r)

def parse_and_validate(payload: str, schema_path: str):
    # Some models return extra text — try to isolate JSON
    text = payload.strip()
    # crude fence stripping
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    # try JSON
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMError(f"Model did not return valid JSON. First 300 chars: {text[:300]}") from e
    schema = json.loads(Path(schema_path).read_text())
    validate(instance=data, schema=schema)
    return data

def save_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2))
    return path

