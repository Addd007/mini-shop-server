from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class TestContext:
    values: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        self.values[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def update(self, data: Dict[str, Any]) -> None:
        self.values.update(data)

    def resolve(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._resolve_string(value)
        if isinstance(value, dict):
            return {k: self.resolve(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.resolve(item) for item in value]
        return value

    def _resolve_string(self, value: str) -> str:
        result = value
        for key, stored in self.values.items():
            token = f"${{{key}}}"
            if token in result:
                result = result.replace(token, str(stored))
        return result
