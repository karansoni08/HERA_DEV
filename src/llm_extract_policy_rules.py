# src/llm_extract_policy_rules.py
from pathlib import Path
import json
from jsonschema import validate, ValidationError
from llm_utils import call_model, parse_and_validate, save_json

PROMPT = Path("src/prompts/policy_extract.txt").read_text()
SCHEMA_PATH = "src/schemas/policy_rules.schema.json"

def try_autofix_missing_policy_name(raw_text: str, fallback_name: str):
    """
    Common model mistake: returns {"Acceptable Use Policy": "...", "controls":[...]}
    This converts it to {"policy_name":"Acceptable Use Policy","controls":[...]}.
    """
    text = raw_text.strip().strip("`")
    if text.startswith("json"):
        text = text[4:].strip()
    data = json.loads(text)

    if "policy_name" not in data:
        # detect a single non-'controls' string key as the policy name
        candidate_keys = [k for k, v in data.items() if k != "controls" and isinstance(v, str)]
        if len(candidate_keys) == 1 and "controls" in data:
            title_key = candidate_keys[0]
            data = {"policy_name": title_key, "controls": data["controls"]}
        else:
            # fallback: inject provided name if controls exist
            if "controls" in data:
                data["policy_name"] = fallback_name
            else:
                # give up and let validation fail with a clear message
                pass
    return data

def run(policy_text: str, policy_name: str = "Acceptable Use Policy"):
    prompt = PROMPT.replace("<<<POLICY>>>", policy_text)
    resp = call_model(prompt)

    # First, try strict parse+validate
    try:
        obj = parse_and_validate(resp, SCHEMA_PATH)
    except Exception:
        # Attempt to fix the common "title-as-key" issue
        fixed = try_autofix_missing_policy_name(resp, policy_name)
        # Validate after fix (raises if still invalid)
        schema = json.loads(Path(SCHEMA_PATH).read_text())
        validate(instance=fixed, schema=schema)
        obj = fixed

    out = save_json(obj, Path(f"outputs/policy/{policy_name.replace(' ','_').lower()}.json"))
    print(f"✅ policy JSON: {out}")

if __name__ == "__main__":
    sample = "Employees must not share credentials; report suspected phishing within 24h; MFA required for remote access."
    run(sample, "Acceptable Use Policy")

