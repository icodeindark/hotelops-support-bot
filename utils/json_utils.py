import json
from pathlib import Path

def load_json(file_path: str):
    path = Path(file_path)
    if not path.exists():
        return []
    with open(file_path, "r") as f:
        return json.load(f)

def save_json(file_path: str, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
