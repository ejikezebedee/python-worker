from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from utils.supabase_client import get_supabase_admin


REVIEW_THRESHOLD = 0.7


def seed_review_task(opportunity_id: str, project_id: str | None = None) -> dict[str, Any] | None:
    supabase = get_supabase_admin()
    opp_resp = supabase.table("opportunities").select("id, quality_score").eq("id", opportunity_id).single().execute()
    opportunity = opp_resp.data
    if not opportunity:
        raise ValueError(f"Opportunity {opportunity_id} not found")

    if float(opportunity.get("quality_score", 0.0)) >= REVIEW_THRESHOLD:
        return None

    existing = supabase.table("review_tasks").select("id").eq("opportunity_id", opportunity_id).limit(1).execute()
    if existing.data:
        return existing.data[0]

    payload = {
        "opportunity_id": opportunity_id,
        "project_id": project_id,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = supabase.table("review_tasks").insert(payload).execute()
    return result.data[0] if result.data else None
