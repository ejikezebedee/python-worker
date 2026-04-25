from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from adapters.rss_adapter import RSSAdapter
from normalizers.dedupe import compute_canonical_hash
from normalizers.schema import OpportunityCreate
from utils.supabase_client import get_supabase_admin


ADAPTERS = {
    "rss": RSSAdapter,
}


def _coerce_datetime(value: Any):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None
    return None


def ingest_source(source_id: str) -> dict[str, Any]:
    supabase = get_supabase_admin()

    source_resp = supabase.table("sources").select("*").eq("id", source_id).single().execute()
    source = source_resp.data
    if not source:
        raise ValueError(f"Source {source_id} not found")

    run_resp = supabase.table("ingestion_runs").insert({
        "source_id": source_id,
        "status": "running",
    }).execute()
    run_id = run_resp.data[0]["id"]

    adapter_cls = ADAPTERS.get(source["type"])
    if not adapter_cls:
        raise ValueError(f"Unsupported source type: {source['type']}")

    adapter = adapter_cls()
    raw_items = adapter.fetch(source.get("config", {}))

    new_count = 0
    try:
        for raw in raw_items:
            opp = OpportunityCreate(
                source_id=source_id,
                external_id=raw.get("external_id"),
                url=raw.get("url"),
                title=raw.get("title", "Untitled opportunity"),
                description=raw.get("description"),
                company_name=raw.get("company_name"),
                location=raw.get("location"),
                posted_at=_coerce_datetime(raw.get("posted_at")),
                raw_data=raw.get("raw_data", raw),
            )

            payload = opp.model_dump(mode="json")
            payload["canonical_hash"] = compute_canonical_hash(
                payload.get("title"),
                payload.get("company_name"),
                payload.get("location"),
                payload.get("url"),
            )

            result = supabase.table("opportunities").upsert(
                payload,
                on_conflict="source_id,external_id",
            ).execute()

            if result.data:
                new_count += 1

        supabase.table("ingestion_runs").update({
            "status": "completed",
            "records_fetched": len(raw_items),
            "records_new": new_count,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", run_id).execute()

        supabase.table("sources").update({
            "last_run_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", source_id).execute()

        return {
            "source_id": source_id,
            "run_id": run_id,
            "records_fetched": len(raw_items),
            "records_new": new_count,
        }
    except Exception as exc:
        supabase.table("ingestion_runs").update({
            "status": "failed",
            "error_log": str(exc),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", run_id).execute()
        raise
