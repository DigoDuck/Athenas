"""Session events (spec 3.2, 4.11), reading (4.4.5, 4.8.1, 4.8.4), practice (4.8.3), home (4.5)."""

from content.models import Attempt, Block, ReviewLog
from content.services import reviews_today
from django.db import transaction
from django.db.models.functions import TruncDate
from django.utils import timezone
from organization.models import Subtopic, Track
from organization.services import next_step

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
            # The first read is the one kept (D-015). After a re-import since the block was
            # opened, `block_order` may name other text, so nothing is marked (D-023).
            Block.objects.filter(
                content__subtopic_id=event.subtopic_id,
                content__updated_at__lte=event.started_at,
                order=event.block_order,
                read_at=None,
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


# A return session opens after this many full days without one and offers at most this many
# reviews (spec 4.7).
RETURN_AFTER_DAYS = 3
RETURN_SESSION_REVIEWS = 5


def in_return_session(*, now=None) -> bool:
    """The first 5 reviews of a day after 3 or more full Bahia days without a session (4.7)."""
    today = timezone.localdate(now)
    earlier = [day for day in session_days() if day < today]
    # Last session on Monday: Tuesday to Thursday are the full days, so Friday returns.
    if not earlier or (today - max(earlier)).days - 1 < RETURN_AFTER_DAYS:
        return False
    # Each card rated completes its own review event (D-025), so reviews end the return session
    # by count; any other activity completed today ends it at once (DECISIONS.md D-026).
    studied = SessionEvent.objects.exclude(completed_at=None).exclude(kind=Kind.REVIEW_SESSION)
    if studied.filter(completed_at__date=today).exists():
        return False
    reviewed = ReviewLog.objects.filter(reviewed_at__date=today).values("flashcard").distinct()
    return reviewed.count() < RETURN_SESSION_REVIEWS


def review_cap_today(*, now=None):
    """The return session's cap, or None for the normal caps (DECISIONS.md D-026)."""
    return RETURN_SESSION_REVIEWS if in_return_session(now=now) else None


def open_home(*, now=None) -> dict:
    """Records `app_opened` (spec Q2) and returns what the home screen shows (spec 4.5.2)."""
    returning = in_return_session(now=now)
    start_activity(Kind.APP_OPENED)
    return {
        "return_session": returning,
        "last_stop": _last_stop(),
        # The return session is only the point where Diogo stopped and its reviews (spec 4.7).
        "next_steps": [] if returning else _next_steps(),
        "reviews_today": reviews_today(now=now, cap=RETURN_SESSION_REVIEWS if returning else None),
    }


def _last_stop():
    latest = (
        SessionEvent.objects.filter(kind=Kind.READING)
        .select_related("subtopic__concept")
        .order_by("-started_at", "-id")
        .first()
    )
    if latest is None:
        return None
    subtopic = latest.subtopic
    block = Block.objects.filter(
        content__subtopic=subtopic, order=resume_block_order(subtopic)
    ).first()
    return {
        "subtopic": subtopic.id,
        "subtopic_name": subtopic.name,
        "concept_name": subtopic.concept.name,
        # A preamble block has no heading (D-014); a re-import may have left no block at all.
        "block_heading": (block.heading or block.kind) if block else "",
    }


def _next_steps():
    """Each track's next step, with the first subtopic of its concept still to finish."""
    steps = []
    for track in Track.objects.prefetch_related("steps__concept__subtopics"):
        step = next_step(track)
        if step is None:
            continue
        subtopic = next(
            (
                s
                for s in step.concept.subtopics.all()
                if s.study_status != Subtopic.StudyStatus.COMPLETED
            ),
            None,
        )
        steps.append(
            {
                "track_name": track.name,
                "concept_name": step.concept.name,
                "subtopic": subtopic.id if subtopic else None,
                "subtopic_name": subtopic.name if subtopic else "",
            }
        )
    return steps
