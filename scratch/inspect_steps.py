import json
from pathlib import Path

p = Path(r"C:\Users\leonc\.gemini\antigravity-ide\brain\fdd8aba2-e8cb-4ee6-9ac2-1677e11162f0\.system_generated\logs\transcript.jsonl")
if p.exists():
    for line in open(p, "r", encoding="utf-8"):
        data = json.loads(line)
        idx = data.get("step_index", 0)
        tc = data.get("tool_calls", [])
        for c in tc:
            args = str(c.get("args", {}))
            if "modelo_ml.py" in args and c.get("name") in ["replace_file_content", "write_to_file", "multi_replace_file_content"]:
                print(f"Step {idx}: {c.get('name')}")
