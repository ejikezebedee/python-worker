from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from adapters.base import BaseAdapter


DATE_PATTERN = re.compile(r"^(\d{1,2}\.\d{1,2}\.\d{4}|\d{4}-\d{2}-\d{2}|[A-Za-z]+\s+\d{1,2},\s*\d{4})$")


class HTMLAdapter(BaseAdapter):
    def fetch(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        page_url = config.get("page_url")
        mode = config.get("mode", "selectors")
        default_company_name = config.get("default_company_name")
        default_location = config.get("default_location")

        response = httpx.get(
            page_url,
            timeout=30.0,
            headers={"User-Agent": "OpenClaw Opportunity Intelligence/1.0"},
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        if mode == "dated_paragraph_stream":
            paragraph_selector = config.get("paragraph_selector", "div p")
            link_selector = config.get("link_selector", "a")
            paragraphs = [p.get_text(" ", strip=True) for p in soup.select(paragraph_selector)]
            items = []
            i = 0
            while i < len(paragraphs):
                current = paragraphs[i].strip()
                if not current:
                    i += 1
                    continue
                if DATE_PATTERN.match(current) and i + 1 < len(paragraphs):
                    title = paragraphs[i + 1].strip()
                    description_parts = []
                    j = i + 2
                    while j < len(paragraphs):
                        nxt = paragraphs[j].strip()
                        if DATE_PATTERN.match(nxt):
                            break
                        if nxt:
                            description_parts.append(nxt)
                        j += 1
                    link = None
                    for p in soup.select(paragraph_selector):
                        txt = p.get_text(" ", strip=True)
                        if txt.strip() == title:
                            a = p.select_one(link_selector)
                            if a and a.has_attr("href"):
                                link = urljoin(page_url, str(a["href"]).strip())
                            break
                    description = " ".join(description_parts).strip() or None
                    items.append({
                        "external_id": link or f"{current}:{title}",
                        "url": link,
                        "title": title,
                        "description": description,
                        "company_name": default_company_name,
                        "location": default_location,
                        "raw_data": {
                            "date": current,
                            "title": title,
                            "url": link,
                            "description": description,
                            "page_url": page_url,
                        },
                    })
                    i = j
                    continue
                i += 1
            return items

        item_selector = config.get("item_selector")
        title_selector = config.get("title_selector")
        link_selector = config.get("link_selector")
        description_selector = config.get("description_selector")

        if not page_url or not item_selector or not title_selector:
            raise ValueError("page_url, item_selector, and title_selector are required for HTMLAdapter")

        items = []
        for item in soup.select(item_selector):
            title_el = item.select_one(title_selector)
            if not title_el:
                continue

            link_el = item.select_one(link_selector) if link_selector else title_el.find("a")
            desc_el = item.select_one(description_selector) if description_selector else None

            title = title_el.get_text(" ", strip=True)
            href = None
            if link_el and link_el.has_attr("href"):
                href = str(link_el["href"]).strip()
                if href:
                    href = urljoin(page_url, href)

            description = desc_el.get_text(" ", strip=True) if desc_el else None
            external_id = href or title

            items.append(
                {
                    "external_id": external_id,
                    "url": href,
                    "title": title,
                    "description": description,
                    "company_name": default_company_name,
                    "location": default_location,
                    "raw_data": {
                        "title": title,
                        "url": href,
                        "description": description,
                        "page_url": page_url,
                    },
                }
            )

        return items
