"""Session events (spec 3.2, 4.11), reading (spec 4.4.5, 4.8.1, 4.8.4) and practice (4.8.3)."""

from content.models import Attempt, Block
from django.db import transaction
from django.db.models.functions import TruncDate
from django.utils import timezone
from organization.models import Subtopic

from .models import SessionEvent

Kind = SessionEvent.Kind

# What each kind of event references, and nothing else (DECISIONS.md D-017).
SUBJECTS = {
    Kind.READING: {"subtopic", "block_order"},
    Kind.NOTEBOOK: {"subtopic"},
    Kind.EXPLANATION: {"subtopic"},
    Kind.QUESTION: {"question"},
    Kind.REVIEW_SESSION: set(),
    Kind.APP_OPENED: set(),
}


@transaction.atomic
def start_activity(kind, *, subtopic=None, question=None, block_order=None) -> SessionEvent:
    subjects = {"subtopic": subtopic, "question": question, "block_order": block_order}
    given = {name for name, value in subjects.items() if value is not None}
    if given != SUBJECTS[kind]:
        expected = ", ".join(sorted(SUBJECTS[kind])) or "nada"
        raise ValueError(f"Um evento {kind} referencia: {expected}.")
    if kind == Kind.READING:
        _open_block(subtopic, block_order)
    return SessionEvent.objects.create(kind=kind, **subjects)


def _open_block(subtopic, order):
    if not Block.objects.filter(content__subtopic=subtopic, order=order).exists():
        raise ValueError(f"O bloco {order} não existe neste subtema.")
    # Opening any block starts the subtopic; this never moves it back (spec 4.4.5).
    started = Subtopic.objects.filter(
        pk=subtopic.pk, study_status=Subtopic.StudyStatus.NOT_STARTED
    ).update(study_status=Subtopic.StudyStatus.IN_PROGRESS)
    if started:
        subtopic.study_status = Subtopic.StudyStatus.IN_PROGRESS


def complete_activity(event) -> None:
    """Finishing is the one change a history row allows, and only once (DECISIONS.md D-020)."""
    if event.kind == Kind.APP_OPENED:
        raise ValueError("Abrir o app não é uma atividade para concluir.")
    now = timezone.now()
    with transaction.atomic():
        pending = SessionEvent.objects.filter(pk=event.pk, completed_at=None)
        if not pending.update(ended_at=now, completed_at=now):
            raise ValueError("Esta atividade já foi concluída.")
        if event.kind == Kind.READING:
            # The first read is the one kept (DECISIONS.md D-015).
            Block.objects.filter(
                content__subtopic_id=event.subtopic_id, order=event.block_order, read_at=None
            ).update(read_at=now)
    event.ended_at = event.completed_at = now


@transaction.atomic
def record_attempt(event, *, text, self_assessment) -> Attempt:
    """Saving the answer finishes its activity, so no attempt exists without a session."""
    if event.kind not in (Kind.QUESTION, Kind.EXPLANATION):
        raise ValueError("Só uma pergunta ou uma explicação recebe tentativa.")
    complete_activity(event)
    question = event.question
    return Attempt.objects.create(
        subtopic_id=question.subtopic_id if question else event.subtopic_id,
        kind=event.kind,
        question=question,
        text=text,
        self_assessment=self_assessment,
    )


def resume_block_order(subtopic) -> int:
    """The block of the latest reading event, so closing the browser loses nothing (4.8.4)."""
    latest = subtopic.events.filter(kind=Kind.READING).order_by("-started_at", "-id").first()
    if latest is None:
        return 0
    # A re-import can leave fewer blocks than the event points at (DECISIONS.md D-017).
    last = Block.objects.filter(content__subtopic=subtopic).count() - 1
    return max(0, min(latest.block_order, last))


def session_days() -> set:
    """Bahia calendar days with at least one completed activity (spec 3.1, 4.11.2)."""
    completed = SessionEvent.objects.exclude(completed_at=None)
    # TruncDate uses the current time zone, America/Bahia, never the UTC date.
    return set(completed.annotate(day=TruncDate("completed_at")).values_list("day", flat=True))
