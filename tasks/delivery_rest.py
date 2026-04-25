from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tasks.matching_rest import match_opportunity_to_projects_rest
from utils.supabase_rest import SupabaseRestClient


DEFAULT_DELIVERY_METHOD = 'csv'


def create_delivery_events_rest(opportunity_id: str) -> list[dict[str, Any]]:
    client = SupabaseRestClient()
    matches = match_opportunity_to_projects_rest(opportunity_id)
    created: list[dict[str, Any]] = []

    for match in matches:
        existing = client.select('delivery_events', 'id', opportunity_id=opportunity_id, project_id=match['project_id'])
        if existing:
            continue

        payload: dict[str, Any] = {
            'opportunity_id': opportunity_id,
            'project_id': match['project_id'],
            'delivery_method': DEFAULT_DELIVERY_METHOD,
            'status': 'pending',
            'metadata': {
                'match_score': match['score'],
                'created_by': 'matching-engine',
                'created_at': datetime.now(timezone.utc).isoformat(),
            },
        }
        result = client.insert('delivery_events', payload)
        if result:
            created.append(result[0])

    return created
