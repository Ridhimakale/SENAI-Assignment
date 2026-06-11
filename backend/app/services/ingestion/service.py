from dataclasses import dataclass
from datetime import UTC

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import JobStatus
from app.models.processing_job import ProcessingJob
from app.repositories.audit import AuditRepository
from app.repositories.ingestion import IngestionRepository
from app.schemas.ingestion import EmailIngestRequest, EmailIngestResponse, ProcessingStatusResponse
from app.services.intelligence.contact_enrichment import enrich_contact_profile
from app.services.intelligence.heuristics import evaluate_email_heuristics
from app.services.intelligence.scenarios import evaluate_special_scenarios, merge_scenario_flags
from app.services.ingestion.normalization import normalize_email_body, normalize_text
from app.services.ingestion.priority import calculate_priority_score


@dataclass(frozen=True)
class IngestionService:
    session: AsyncSession

    async def ingest_email(self, request: EmailIngestRequest) -> EmailIngestResponse:
        repository = IngestionRepository(self.session)
        audit_repository = AuditRepository(self.session)

        timestamp = request.timestamp
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        else:
            timestamp = timestamp.astimezone(UTC)

        existing = await repository.find_email_with_job(request.message_id)
        if existing is not None:
            email, job = existing
            await audit_repository.create_event(
                entity_type="email",
                entity_id=email.id,
                action="EMAIL_DEDUPLICATED",
                diff={"message_id": request.message_id},
            )
            await self.session.commit()
            return EmailIngestResponse(
                job_id=job.job_id if job else "unknown",
                email_id=email.id,
                message_id=email.message_id,
                deduplicated=True,
                status=email.status.value,
                priority_score=email.priority_score,
            )

        normalized_subject = normalize_text(request.subject)
        normalized_body = normalize_email_body(request.body)
        priority_score, heuristic_flags = calculate_priority_score(
            normalized_subject, normalized_body.body
        )
        heuristic_flags["empty_body"] = normalized_body.is_empty
        heuristic_flags["body_over_10000_chars"] = normalized_body.is_truncated_for_llm

        job = await repository.create_processing_job()
        contact = await repository.get_or_create_contact(request.sender, timestamp)
        thread = await repository.get_or_create_thread(
            external_thread_id=request.thread_id,
            contact=contact,
            sender=request.sender,
            subject=normalized_subject,
            timestamp=timestamp,
        )
        email = await repository.create_email(
            thread=thread,
            contact=contact,
            job=job,
            message_id=request.message_id,
            sender=request.sender,
            subject=normalize_text(request.subject),
            normalized_subject=normalized_subject.lower(),
            body=normalized_body.body,
            body_preview=normalized_body.preview,
            body_truncated=normalized_body.is_truncated_for_llm,
            timestamp=timestamp,
            priority_score=priority_score,
            heuristic_flags=heuristic_flags,
        )
        heuristic_result = evaluate_email_heuristics(
            sender=request.sender,
            subject=normalized_subject,
            body=normalized_body.body,
        )
        email.category = heuristic_result.category
        email.urgency = heuristic_result.urgency
        email.status = heuristic_result.status
        email.requires_human = heuristic_result.requires_human
        email.heuristic_flags = {
            **heuristic_flags,
            **heuristic_result.flags,
            "stop_processing": heuristic_result.stop_processing,
        }
        scenario_evaluation = evaluate_special_scenarios(email=email, thread_history=[email])
        email.heuristic_flags = merge_scenario_flags(
            email.heuristic_flags, scenario_evaluation
        )
        if scenario_evaluation.scenarios:
            email.requires_human = (
                email.requires_human or scenario_evaluation.flags["scenario_requires_human"]
            )
            if scenario_evaluation.highest_urgency == email.urgency:
                pass
            elif scenario_evaluation.highest_urgency is not None:
                email.urgency = scenario_evaluation.highest_urgency
        job.stage = "HEURISTIC_PREFILTER"
        if heuristic_result.stop_processing:
            job.status = JobStatus.COMPLETED
        await self.session.flush()

        if heuristic_result.action_type is not None and heuristic_result.action_reason:
            await repository.create_triage_action(
                email=email,
                action_type=heuristic_result.action_type,
                reason=heuristic_result.action_reason,
            )

        await repository.update_thread_after_email(
            thread=thread,
            timestamp=timestamp,
            priority_score=priority_score,
        )
        await audit_repository.create_event(
            entity_type="email",
            entity_id=email.id,
            action="HEURISTIC_APPLIED",
            diff={
                "category": email.category.value if email.category else None,
                "urgency": email.urgency.value if email.urgency else None,
                "status": email.status.value,
                "requires_human": email.requires_human,
                "stop_processing": heuristic_result.stop_processing,
            },
            correlation_id=job.job_id,
        )
        if scenario_evaluation.scenarios:
            await audit_repository.create_event(
                entity_type="email",
                entity_id=email.id,
                action="SCENARIO_DETECTED",
                diff=scenario_evaluation.flags,
                correlation_id=job.job_id,
            )
        contact_emails = await repository.get_contact_emails(contact.id)
        enrichment = enrich_contact_profile(
            contact=contact,
            emails=contact_emails,
            scenario_evaluation=scenario_evaluation,
        )
        contact = await repository.update_contact_profile(
            contact,
            account_value=enrichment.account_value,
            churn_risk_score=enrichment.churn_risk_score,
            subscription_tier=enrichment.subscription_tier,
            renewal_status=enrichment.renewal_status,
            vip_reason=enrichment.vip_reason,
            status=enrichment.status,
            metadata_json=enrichment.metadata_json,
            open_ticket_count=await repository.count_open_tickets_for_contact(contact.id),
        )
        await audit_repository.create_event(
            entity_type="contact",
            entity_id=contact.id,
            action="CONTACT_ENRICHED",
            diff={
                "account_value": str(contact.account_value) if contact.account_value is not None else None,
                "churn_risk_score": contact.churn_risk_score,
                "subscription_tier": contact.subscription_tier,
                "renewal_status": contact.renewal_status,
                "vip_reason": contact.vip_reason,
                "status": contact.status.value,
            },
            correlation_id=job.job_id,
        )
        await audit_repository.create_event(
            entity_type="email",
            entity_id=email.id,
            action="EMAIL_INGESTED",
            diff={
                "message_id": email.message_id,
                "thread_id": request.thread_id,
                "priority_score": priority_score,
            },
            correlation_id=job.job_id,
        )

        await self.session.commit()
        return EmailIngestResponse(
            job_id=job.job_id,
            email_id=email.id,
            message_id=email.message_id,
            deduplicated=False,
            status=job.status.value,
            priority_score=priority_score,
        )

    async def get_status(self, job_id: str) -> ProcessingStatusResponse | None:
        repository = IngestionRepository(self.session)
        job = await repository.get_processing_job_by_job_id(job_id)
        if job is None:
            return None
        return _status_response(job)


def _status_response(job: ProcessingJob) -> ProcessingStatusResponse:
    return ProcessingStatusResponse(
        job_id=job.job_id,
        email_id=job.email.id if job.email else None,
        status=job.status.value,
        stage=job.stage,
        error_code=job.error_code,
        error_message=job.error_message,
        updated_at=job.updated_at,
    )
