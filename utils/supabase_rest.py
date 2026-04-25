from __future__ import annotations

import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


class SupabaseRestClient:
    def __init__(self) -> None:
        self.base_url = os.environ["SUPABASE_URL"].rstrip("/")
        self.api_key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        self.rest_url = f"{self.base_url}/rest/v1"
        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def select(self, table: str, columns: str = "*", **filters: Any) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"select": columns}
        for key, value in filters.items():
            params[key] = f"eq.{value}"
        response = httpx.get(f"{self.rest_url}/{table}", headers=self.headers, params=params, timeout=30.0)
        response.raise_for_status()
        return response.json()

    def insert(self, table: str, payload: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        response = httpx.post(f"{self.rest_url}/{table}", headers=self.headers, json=payload, timeout=30.0)
        response.raise_for_status()
        return response.json()

    def upsert(self, table: str, payload: dict[str, Any] | list[dict[str, Any]], on_conflict: str) -> list[dict[str, Any]]:
        headers = {**self.headers, "Prefer": "resolution=merge-duplicates,return=representation"}
        response = httpx.post(
            f"{self.rest_url}/{table}",
            headers=headers,
            params={"on_conflict": on_conflict},
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    def update(self, table: str, filters: dict[str, Any], payload: dict[str, Any]) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        for key, value in filters.items():
            params[key] = f"eq.{value}"
        response = httpx.patch(f"{self.rest_url}/{table}", headers=self.headers, params=params, json=payload, timeout=30.0)
        response.raise_for_status()
        return response.json()
