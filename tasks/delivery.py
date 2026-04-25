from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tasks.matching import match_opportunity_to_projects
from utils.supabase_client import get_supabase_admin


DEFAULT_DELIVERY_METHOD = "csv"


def create_delivery_events(opportunity_id: str) -> list[dict[str, Any]]:
    supabase = get_supabase_admin()
    matches = match_opportunity_to_projects(opportunity_id)
    created: list[dict[str, Any]] = []

    for match in matches:
        existing = supabase.table("delivery_events").select("id").eq("opportunity_id", opportunity_id).eq("project_id", match["project_id"]).limit(1).execute()
        if existing.data:
            continue

        payload: dict[str, Any] = {
            "opportunity_id": opportunity_id,
            "project_id": match["project_id"],
            "delivery_method": DEFAULT_DELIVERY_METHOD,
            "status": "pending",
            "metadata": {
                "match_score": match["score"],
                "created_by": "matching-engine",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        result = supabase.table("delivery_events").insert(payload).execute()
        if result.data:
            created.append(result.data[0])

    return created
