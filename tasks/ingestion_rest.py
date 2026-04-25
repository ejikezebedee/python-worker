from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from adapters.html_adapter import HTMLAdapter
from adapters.rss_adapter import RSSAdapter
from normalizers.dedupe import compute_canonical_hash
from normalizers.schema import OpportunityCreate
from utils.supabase_rest import SupabaseRestClient


ADAPTERS = {
    "rss": RSSAdapter,
    "html": HTMLAdapter,
}


def _coerce_datetime(value: Any):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            return None
    return None


def ingest_source_rest(source_id: str) -> dict[str, Any]:
    client = SupabaseRestClient()

    sources = client.select('sources', '*', id=source_id)
    if not sources:
        raise ValueError(f'Source {source_id} not found')
    source = sources[0]

    run = client.insert('ingestion_runs', {
        'source_id': source_id,
        'status': 'running',
    })[0]
    run_id = run['id']

    adapter_cls = ADAPTERS.get(source['type'])
    if not adapter_cls:
        raise ValueError(f"Unsupported source type: {source['type']}")

    adapter = adapter_cls()
    raw_items = adapter.fetch(source.get('config', {}))

    new_count = 0
    try:
        for raw in raw_items:
            opp = OpportunityCreate(
                source_id=source_id,
                external_id=raw.get('external_id'),
                url=raw.get('url'),
                title=raw.get('title', 'Untitled opportunity'),
                description=raw.get('description'),
                company_name=raw.get('company_name'),
                location=raw.get('location'),
                posted_at=None,
                raw_data=raw.get('raw_data', raw),
            )
            payload = opp.model_dump(mode='json')
            payload['posted_at'] = _coerce_datetime(raw.get('posted_at'))
            payload['canonical_hash'] = compute_canonical_hash(
                payload.get('title'),
                payload.get('company_name'),
                payload.get('location'),
                payload.get('url'),
            )

            existing = []
            if payload.get('external_id'):
                existing = client.select(
                    'opportunities',
                    'id',
                    source_id=source_id,
                    external_id=payload['external_id'],
                )
            if existing:
                continue

            result = client.insert('opportunities', payload)
            if result:
                new_count += 1

        client.update('ingestion_runs', {'id': run_id}, {
            'status': 'completed',
            'records_fetched': len(raw_items),
            'records_new': new_count,
            'finished_at': datetime.now(timezone.utc).isoformat(),
        })
        client.update('sources', {'id': source_id}, {
            'last_run_at': datetime.now(timezone.utc).isoformat(),
        })
        return {
            'source_id': source_id,
            'run_id': run_id,
            'records_fetched': len(raw_items),
            'records_new': new_count,
        }
    except Exception as exc:
        client.update('ingestion_runs', {'id': run_id}, {
            'status': 'failed',
            'error_log': str(exc),
            'finished_at': datetime.now(timezone.utc).isoformat(),
        })
        raise
