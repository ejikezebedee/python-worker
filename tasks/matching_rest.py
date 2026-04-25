from __future__ import annotations

from typing import Any

from utils.supabase_rest import SupabaseRestClient


MATCH_THRESHOLD = 2
GENERIC_KEYWORDS = {
    'germany',
    'german',
    'deutschland',
    'europe',
    'european',
    'global',
    'international',
    'business',
    'opportunities',
    'opportunity',
    'market',
    'company',
    'companies',
    'finance',
}


def _normalize_text(value: Any) -> str:
    if not value:
        return ''
    if isinstance(value, list):
        return ' '.join(str(item) for item in value).lower()
    return str(value).lower()


def _score_match(opportunity: dict[str, Any], project: dict[str, Any]) -> int:
    title = _normalize_text(opportunity.get('title'))
    description = _normalize_text(opportunity.get('description'))
    company_name = _normalize_text(opportunity.get('company_name'))
    location = _normalize_text(opportunity.get('location'))
    skills = _normalize_text(opportunity.get('skills') or [])
    haystack = ' '.join([title, description, company_name, location, skills])

    keywords = [keyword.lower().strip() for keyword in project.get('target_keywords') or [] if keyword and keyword.lower().strip() not in GENERIC_KEYWORDS]

    score = 0
    strong_hits = 0
    for keyword in keywords:
        if keyword and keyword in haystack:
            score += 1
            if keyword in title or keyword in company_name:
                strong_hits += 1

    if strong_hits >= 1:
        score += 1

    return score


def match_opportunity_to_projects_rest(opportunity_id: str) -> list[dict[str, Any]]:
    client = SupabaseRestClient()
    opportunities = client.select('opportunities', '*', id=opportunity_id)
    if not opportunities:
        raise ValueError(f'Opportunity {opportunity_id} not found')
    opportunity = opportunities[0]

    projects = client.select('projects', '*', status='active')

    matches: list[dict[str, Any]] = []
    for project in projects:
        score = _score_match(opportunity, project)
        if score >= MATCH_THRESHOLD:
            matches.append({'project_id': project['id'], 'score': score})
    return matches
