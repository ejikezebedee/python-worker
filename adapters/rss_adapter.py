from __future__ import annotations

from typing import Any

import feedparser

from adapters.base import BaseAdapter


class RSSAdapter(BaseAdapter):
    def fetch(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        feed_url = config.get("feed_url")
        if not feed_url:
            raise ValueError("feed_url is required for RSSAdapter")

        parsed = feedparser.parse(feed_url)
        items: list[dict[str, Any]] = []
        for entry in parsed.entries:
            items.append(
                {
                    "external_id": entry.get("id") or entry.get("link"),
                    "url": entry.get("link"),
                    "title": entry.get("title", "Untitled opportunity"),
                    "description": entry.get("summary") or entry.get("description"),
                    "company_name": config.get("default_company_name"),
                    "location": config.get("default_location"),
                    "posted_at": entry.get("published") or entry.get("updated"),
                    "raw_data": dict(entry),
                }
            )
        return items
