"""Study status and completion (spec 4.4, DECISIONS.md D-024) and the next step (spec 4.5.1)."""

from content.models import Attempt, Block
from django.db import transaction

from .models import Subtopic

Status = Subtopic.StudyStatus
PASSING = [Attempt.SelfAssessment.RIGHT, Attempt.SelfAssessment.PARTIAL]


def completion_suggested(subtopic) -> bool:
    """Every block read and one attempt rated right or partial; never for an empty subtopic."""
    if subtopic.study_status == Status.COMPLETED:
        return False
    blocks = Block.objects.filter(content__subtopic=subtopic)
    return (
        blocks.exists()
        and not blocks.filter(read_at=None).exists()
        and subtopic.attempts.filter(self_assessment__in=PASSING).exists()
    )


@transaction.atomic
def complete_subtopic(subtopic) -> None:
    """Diogo's confirmation, the only way a suggestion becomes a status (spec 4.4.2)."""
    # The lock makes a second click wait and then see the subtopic already completed.
    locked = Subtopic.objects.select_for_update().get(pk=subtopic.pk)
    if not completion_suggested(locked):
        raise ValueError("Este subtema não está sugerido para conclusão.")
    locked.study_status = Status.COMPLETED
    locked.save(update_fields=["study_status"])
    subtopic.study_status = Status.COMPLETED


def reopen_subtopic(subtopic) -> None:
    reopened = Subtopic.objects.filter(pk=subtopic.pk, study_status=Status.COMPLETED).update(
        study_status=Status.IN_PROGRESS
    )
    if not reopened:
        raise ValueError("Só um subtema concluído pode ser reaberto.")
    subtopic.study_status = Status.IN_PROGRESS


def concept_status(concept) -> str:
    """Derived on every read, never stored (spec 4.4.6). `.all()` reuses a prefetch."""
    statuses = {s.study_status for s in concept.subtopics.all()}
    if statuses <= {Status.NOT_STARTED}:
        return Status.NOT_STARTED
    if statuses == {Status.COMPLETED}:
        return Status.COMPLETED
    return Status.IN_PROGRESS


def next_step(track):
    """The first step whose concept is not completed, or None (spec 4.5.1)."""
    return next(
        (s for s in track.steps.all() if concept_status(s.concept) != Status.COMPLETED), None
    )
