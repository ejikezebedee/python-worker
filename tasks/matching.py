from __future__ import annotations

from typing import Any

from utils.supabase_client import get_supabase_admin


MATCH_THRESHOLD = 1


def _score_match(opportunity: dict[str, Any], project: dict[str, Any]) -> int:
    title = (opportunity.get("title") or "").lower()
    description = (opportunity.get("description") or "").lower()
    skills = [skill.lower() for skill in opportunity.get("skills") or []]
    keywords = [keyword.lower() for keyword in project.get("target_keywords") or []]

    score = 0
    for keyword in keywords:
        if keyword in title or keyword in description or keyword in skills:
            score += 1
    return score


def match_opportunity_to_projects(opportunity_id: str) -> list[dict[str, Any]]:
    supabase = get_supabase_admin()
    opp_resp = supabase.table("opportunities").select("*").eq("id", opportunity_id).single().execute()
    opportunity = opp_resp.data
    if not opportunity:
        raise ValueError(f"Opportunity {opportunity_id} not found")

    projects_resp = supabase.table("projects").select("*").eq("status", "active").execute()
    projects = projects_resp.data or []

    matches: list[dict[str, Any]] = []
    for project in projects:
        score = _score_match(opportunity, project)
        if score >= MATCH_THRESHOLD:
            matches.append({
                "project_id": project["id"],
                "score": score,
            })
    return matches
