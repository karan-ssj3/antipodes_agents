from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List


BASE_DIR = Path("outputs/experiments/configs")


@dataclass
class SavedConfig:
    path: str
    name: str
    timestamp: str
    changes: Dict[str, float]
    meta: Dict[str, str]


def _ensure_dirs() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)


def save_variant_config(name: str, changes: Dict[str, float], meta: Dict[str, str] | None = None) -> str:
    _ensure_dirs()
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    safe = name.replace(" ", "_")
    path = BASE_DIR / f"{ts}_{safe}.json"
    payload = {
        "name": name,
        "timestamp": ts,
        "changes": changes,
        "meta": meta or {},
    }
    path.write_text(json.dumps(payload, indent=2))
    return str(path)


def list_saved_configs() -> List[SavedConfig]:
    _ensure_dirs()
    items: List[SavedConfig] = []
    for p in sorted(BASE_DIR.glob("*.json"), reverse=True):
        try:
            obj = json.loads(p.read_text())
            items.append(SavedConfig(path=str(p), name=obj.get("name", p.stem), timestamp=obj.get("timestamp", ""), changes=obj.get("changes", {}), meta=obj.get("meta", {})))
        except Exception:
            continue
    return items


def load_config(path: str) -> Dict[str, float]:
    obj = json.loads(Path(path).read_text())
    return obj.get("changes", {})


