from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    @abstractmethod
    def fetch(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        raise NotImplementedError
