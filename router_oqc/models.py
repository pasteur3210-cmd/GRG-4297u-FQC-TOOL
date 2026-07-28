from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DeviceStatus:
    system: dict[str, str] = field(default_factory=dict)
    lan: dict[str, str] = field(default_factory=dict)
    wan: list[dict[str, str]] = field(default_factory=list)
    raw_url: str = ""

    def get(self, section: str, key: str, default: str = "") -> str:
        source = self.system if section == "system" else self.lan
        return source.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "lan": self.lan,
            "wan": self.wan,
            "raw_url": self.raw_url,
        }
