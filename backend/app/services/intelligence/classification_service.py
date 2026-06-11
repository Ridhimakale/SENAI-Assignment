from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.email import Email
from app.models.enums import (
    ClassificationValidationStatus,
    EmailCategory,
    EmailStatus,
    JobStatus,
)
from app.repositories.audit import AuditRepository
from app.repositories.classification import ClassificationRepository
from app.schemas.classification import ClassificationOutput, ClassificationResponse
from app.services.intelligence.classifier_provider import (
    ClassifierProvider,
    GroqClassifierProvider,
    OpenAIClassifierProvider,
    RuleBasedClassifierProvider,
)
from app.services.intelligence.prompt_builder import build_classification_prompt
from app.services.intelligence.scenarios import evaluate_special_scenarios, merge_scenario_flags
from app.services.rag.service import RagService, get_rag_service


@dataclass
class ClassificationService:
    session: AsyncSession
    rag_service: RagService
    provider: ClassifierProvider
    prompt_version: str
    confidence_threshold: float

    async def classify_email(self, email_id: int) -> ClassificationResponse:
        repository = ClassificationRepository(self.session)
        audit_repository = AuditRepository(self.session)
        email = await repository.get_email_for_classification(email_id)
        if email is None:
            raise ValueError("Email not found.")
        if email.category in (EmailCategory.SPAM, EmailCategory.INTERNAL):
            raise ValueError("Spam and internal emails are not classified by LLM.")
        if _is_critical_security_stop(email):
            raise ValueError("Critical security emails bypass LLM classification.")

        thread_history = await repository.get_thread_history(email)
        scenario_evaluation = evaluate_special_scenarios(
            email=email, thread_history=thread_history
        )
        if scenario_evaluation.scenarios:
            email.heuristic_flags = merge_scenario_flags(
                email.heuristic_flags, scenario_evaluation
            )
            email.requires_human = (
                email.requires_human or scenario_evaluation.flags["scenario_requires_human"]
            )
            if scenario_evaluation.highest_urgency is not None:
                email.urgency = scenario_evaluation.highest_urgency
            await self.session.flush()
        rag_query = _build_rag_query(email, thread_history)
        rag_context = self.rag_service.search(rag_query)
        prompt = build_classification_prompt(
            current_email=email,
            thread_history=thread_history,
            rag_context=rag_context,
        )

        try:
            raw_output = await self.provider.classify(prompt, _email_text(email, thread_history))
            classification = ClassificationOutput.model_validate(raw_output)
            requires_human = (
                classification.requires_human
                or classification.confidence < self.confidence_threshold
            )
            if classification.confidence < self.confidence_threshold:
                classification.requires_human = True
                classification.escalation_reason = (
                    classification.escalation_reason
                    or "Classifier confidence below 0.70 requires human review."
                )
                classification.suggested_reply = None

            output = classification.model_dump(mode="json")
            await repository.create_classification_run(
                email=email,
                prompt_version=self.prompt_version,
                model_name=self.provider.model_name,
                output=output,
                confidence=classification.confidence,
                validation_status=ClassificationValidationStatus.VALID,
            )
            await repository.apply_classification(
                email=email,
                output=output,
                rag_context={
                    "query": rag_context.query,
                    "results": [result.model_dump() for result in rag_context.results],
                },
                requires_human=requires_human,
            )
            await audit_repository.create_event(
                entity_type="email",
                entity_id=email.id,
                action="CLASSIFICATION_COMPLETED",
                diff={
                    "category": output["category"],
                    "urgency": output["urgency"],
                    "confidence": output["confidence"],
                    "requires_human": requires_human,
                    "rag_sources": sorted({result.source_doc for result in rag_context.results}),
                },
            )
            await self.session.commit()
            return ClassificationResponse(
                email_id=email.id,
                classification=classification,
                rag_sources=sorted({result.source_doc for result in rag_context.results}),
                prompt_version=self.prompt_version,
                model_name=self.provider.model_name,
                validation_status=ClassificationValidationStatus.VALID.value,
            )
        except Exception as exc:
            await repository.create_classification_run(
                email=email,
                prompt_version=self.prompt_version,
                model_name=self.provider.model_name,
                output=None,
                confidence=None,
                validation_status=ClassificationValidationStatus.FAILED,
                error_message=str(exc),
            )
            email.requires_human = True
            email.status = EmailStatus.PROCESSING
            email.classification_error = str(exc)
            if email.processing_job:
                email.processing_job.stage = "CLASSIFICATION_FAILED"
                email.processing_job.status = JobStatus.PROCESSING
            await audit_repository.create_event(
                entity_type="email",
                entity_id=email.id,
                action="CLASSIFICATION_FAILED",
                diff={"error": str(exc), "requires_human": True},
            )
            await self.session.commit()
            raise


def create_classification_service(session: AsyncSession) -> ClassificationService:
    settings = get_settings()
    provider: ClassifierProvider
    if settings.groq_api_key:
        provider = GroqClassifierProvider(
            api_key=settings.groq_api_key,
            model_name=settings.groq_model,
        )
    elif settings.openai_api_key:
        provider = OpenAIClassifierProvider(
            api_key=settings.openai_api_key,
            model_name=settings.openai_model,
        )
    else:
        provider = RuleBasedClassifierProvider()
    return ClassificationService(
        session=session,
        rag_service=get_rag_service(),
        provider=provider,
        prompt_version=settings.classifier_prompt_version,
        confidence_threshold=settings.classifier_confidence_threshold,
    )


def _build_rag_query(email: Email, thread_history: list[Email]) -> str:
    recent_context = " ".join(
        f"{item.subject or ''} {item.body}" for item in thread_history[-5:]
    )
    return f"{email.subject or ''} {email.body} {recent_context}"[:4000]


def _email_text(email: Email, thread_history: list[Email]) -> str:
    return " ".join(f"{item.subject or ''} {item.body}" for item in thread_history + [email])


def _is_critical_security_stop(email: Email) -> bool:
    flags = email.heuristic_flags or {}
    return bool(flags.get("is_critical_security") and flags.get("stop_processing"))
