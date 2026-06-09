from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml


class CaseLoader:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)

    def load(self, relative_path: str) -> List[Dict[str, Any]]:
        path = self.base_dir / relative_path
        with path.open("r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
        return loaded or []
