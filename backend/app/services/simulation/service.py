import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from app.schemas.ingestion import EmailIngestRequest
from app.schemas.simulation import (
    EmailStreamSimulationItem,
    EmailStreamSimulationRequest,
    EmailStreamSimulationResponse,
)
from app.services.ingestion.service import IngestionService


@dataclass(frozen=True)
class EmailStreamSimulatorService:
    ingestion_service: IngestionService

    async def run(self, request: EmailStreamSimulationRequest) -> EmailStreamSimulationResponse:
        source_path = self._resolve_source_path(request.source_path)
        payload = self._load_json(source_path)
        emails = self._extract_emails(payload)
        total_loaded = len(emails)

        if request.start_index:
            emails = emails[request.start_index :]
        if request.limit is not None:
            emails = emails[: request.limit]

        if request.dry_run:
            results = [
                EmailStreamSimulationItem(
                    index=index,
                    message_id=item["message_id"],
                    thread_id=item["thread_id"],
                    sender=item["sender"],
                    timestamp=item["timestamp"],
                    status="dry_run",
                    deduplicated=False,
                    job_id=None,
                    email_id=None,
                )
                for index, item in enumerate(emails, start=request.start_index)
            ]
            return EmailStreamSimulationResponse(
                source_path=str(source_path),
                total_loaded=total_loaded,
                processed=len(results),
                succeeded=0,
                failed=0,
                deduplicated=0,
                elapsed_seconds=0.0,
                replay_rate_per_second=request.emails_per_second,
                results=results,
            )

        delay = 1.0 / request.emails_per_second
        started_at = perf_counter()
        results: list[EmailStreamSimulationItem] = []
        succeeded = 0
        failed = 0
        deduplicated = 0

        for index, item in enumerate(emails, start=request.start_index):
            try:
                ingest_request = EmailIngestRequest(
                    message_id=item["message_id"],
                    thread_id=item["thread_id"],
                    sender=item["sender"],
                    subject=item.get("subject", ""),
                    body=item.get("body", ""),
                    timestamp=item["timestamp"],
                )
                ingest_result = await self.ingestion_service.ingest_email(ingest_request)
                succeeded += 1
                if ingest_result.deduplicated:
                    deduplicated += 1
                results.append(
                    EmailStreamSimulationItem(
                        index=index,
                        message_id=ingest_result.message_id,
                        thread_id=item["thread_id"],
                        sender=item["sender"],
                        timestamp=item["timestamp"],
                        status=ingest_result.status,
                        deduplicated=ingest_result.deduplicated,
                        job_id=ingest_result.job_id,
                        email_id=ingest_result.email_id,
                    )
                )
            except Exception as exc:  # noqa: BLE001 - keep replay running unless fail_fast is set
                failed += 1
                results.append(
                    EmailStreamSimulationItem(
                        index=index,
                        message_id=str(item.get("message_id", "")),
                        thread_id=str(item.get("thread_id", "")),
                        sender=str(item.get("sender", "")),
                        timestamp=item["timestamp"],
                        status="failed",
                        deduplicated=False,
                        job_id=None,
                        email_id=None,
                        error=str(exc),
                    )
                )
                if request.fail_fast:
                    break
            if index < request.start_index + len(emails) - 1:
                await asyncio.sleep(delay)

        return EmailStreamSimulationResponse(
            source_path=str(source_path),
            total_loaded=total_loaded,
            processed=len(results),
            succeeded=succeeded,
            failed=failed,
            deduplicated=deduplicated,
            elapsed_seconds=perf_counter() - started_at,
            replay_rate_per_second=request.emails_per_second,
            results=results,
        )

    @staticmethod
    def _resolve_source_path(source_path: str) -> Path:
        candidate = Path(source_path)
        if candidate.is_file():
            return candidate

        repo_root = Path(__file__).resolve().parents[4]
        candidate = repo_root / source_path
        if candidate.is_file():
            return candidate

        raise FileNotFoundError(f"Dataset file not found: {source_path}")

    @staticmethod
    def _load_json(source_path: Path) -> Any:
        with source_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _extract_emails(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            raw_items = payload
        elif isinstance(payload, dict):
            for key in ("emails", "items", "data", "messages"):
                value = payload.get(key)
                if isinstance(value, list):
                    raw_items = value
                    break
            else:
                raise ValueError("Unsupported email dataset format.")
        else:
            raise ValueError("Unsupported email dataset format.")

        normalized_items: list[dict[str, Any]] = []
        for raw in raw_items:
            normalized_items.append(_normalize_raw_email_record(raw))
        return normalized_items


def _normalize_raw_email_record(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("Each email record must be a JSON object.")

    message_id = _first_value(raw, "message_id", "messageId", "id", "msg_id")
    thread_id = _first_value(raw, "thread_id", "threadId", "thread", "conversation_id")
    sender = _first_value(raw, "sender", "from", "from_email", "email")
    timestamp_value = _first_value(raw, "timestamp", "sent_at", "date", "created_at")
    subject = raw.get("subject", "")
    body = raw.get("body", raw.get("text", raw.get("content", "")))

    if message_id is None or thread_id is None or sender is None or timestamp_value is None:
        raise ValueError("Email record is missing a required field.")

    timestamp = _parse_timestamp(timestamp_value)

    return {
        "message_id": str(message_id).strip(),
        "thread_id": str(thread_id).strip(),
        "sender": str(sender).strip(),
        "subject": subject if subject is not None else "",
        "body": body if body is not None else "",
        "timestamp": timestamp,
    }


def _first_value(raw: dict[str, Any], *keys: str) -> Any | None:
    for key in keys:
        if key in raw and raw[key] not in (None, ""):
            return raw[key]
    return None


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        timestamp = value
    elif isinstance(value, str):
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("Unsupported timestamp value.")

    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC)
