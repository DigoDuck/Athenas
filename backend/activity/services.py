"""Session events (spec 3.2, 4.11), reading (4.4.5, 4.8.1, 4.8.4), notebook mode (4.8.2),
practice (4.8.3), review (D-025), the home screen (4.5), the day 28 metric (4.11.2) and the
support metrics (4.11.3)."""

from collections import Counter
from datetime import date, timedelta
from statistics import median

from content.models import Attempt, Block, DailyReviewQueue, PracticeQuestion, ReviewLog
from content.services import rate_card, reviews_today
from django.db import transaction
from django.db.models import Count
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from organization.models import Concept, Subtopic, Track
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


@transaction.atomic
def record_review(event, *, flashcard, rating) -> ReviewLog:
    """Rating the card finishes its review event, so no review exists without a session."""
    if event.kind != Kind.REVIEW_SESSION:
        raise ValueError("Só um evento de revisão recebe a avaliação de um cartão.")
    complete_activity(event)
    return rate_card(flashcard, rating)


def resume_block_order(subtopic) -> int:
    """The block of the latest reading event, so closing the browser loses nothing (4.8.4)."""
    latest = subtopic.events.filter(kind=Kind.READING).order_by("-started_at", "-id").first()
    if latest is None:
        return 0
    # A re-import can leave fewer blocks than the event points at (DECISIONS.md D-017).
    last = Block.objects.filter(content__subtopic=subtopic).count() - 1
    return max(0, min(latest.block_order, last))


# What notebook mode shows, in this order, before its one practice prompt (spec Q16).
NOTEBOOK_BLOCKS = ("Objetivo", "Ideia central", "Exemplo", "Resumo para o caderno")


def notebook(subtopic) -> dict:
    """The notebook blocks that have text, the ones missing, and one question (DECISIONS.md D-036).

    Each finished copy moves one question further in Practice's order, wrapping around, so copying
    the subtopic again asks something else even when every answer stays on paper. It never looks
    at how earlier answers went (spec 2.2). None means "explain in my words".
    """
    blocks = [
        b
        for b in Block.objects.filter(content__subtopic=subtopic, kind__in=NOTEBOOK_BLOCKS)
        if b.body.strip()
    ]
    blocks.sort(key=lambda b: (NOTEBOOK_BLOCKS.index(b.kind), b.order))
    shown = {b.kind for b in blocks}
    # The same questions Practice offers, in its order, so the prompt can be answered there.
    questions = list(
        PracticeQuestion.objects.filter(subtopic=subtopic, archived=False).exclude(
            reference_answer=""
        )
    )
    copies = subtopic.events.filter(kind=Kind.NOTEBOOK).exclude(completed_at=None).count()
    return {
        "blocks": blocks,
        "missing": [kind for kind in NOTEBOOK_BLOCKS if kind not in shown],
        "question": questions[copies % len(questions)] if questions else None,
    }


def session_days() -> set:
    """Bahia calendar days with at least one completed activity (spec 3.1, 4.11.2)."""
    completed = SessionEvent.objects.exclude(completed_at=None)
    # TruncDate uses the current time zone, America/Bahia, never the UTC date.
    return set(completed.annotate(day=TruncDate("completed_at")).values_list("day", flat=True))


# The day 28 window: blocks of 7 Bahia days from day 1, a block counts with 3 days of use, and a
# 2 of 4 gets blocks 5 and 6 as its one extension (DECISIONS.md D-010, D-029 and D-038).
DAY_1 = date(2026, 10, 17)
BLOCK_DAYS = 7
DAYS_TO_MEET = 3
BLOCKS = (1, 2, 3, 4)
EXTENSION = (5, 6)


def day28_block(number, days, *, today) -> dict:
    """One block, `met`, `missed` or `open`, decided as soon as the days left cannot change it."""
    start = DAY_1 + timedelta(days=BLOCK_DAYS * (number - 1))
    dates = [start + timedelta(days=n) for n in range(BLOCK_DAYS)]
    # Read as of `today`: a later day of use did not exist yet on that date.
    used = [day for day in dates if day in days and day <= today]
    # Today is not over, so it can still become a day of use.
    left = sum(1 for day in dates if day >= today and day not in used)
    if len(used) >= DAYS_TO_MEET:
        status = "met"
    elif len(used) + left < DAYS_TO_MEET:
        status = "missed"
    else:
        status = "open"
    return {"number": number, "start": start, "end": dates[-1], "days": used, "status": status}


def day28_metric(days, *, today) -> dict:
    """The D-010 reading of a set of Bahia days of use, read on the Bahia date `today`."""
    blocks = [day28_block(n, days, today=today) for n in BLOCKS]
    met = [b["number"] for b in blocks if b["status"] == "met"]
    possible = [b["number"] for b in blocks if b["status"] != "missed"]
    result = {"blocks": blocks, "extension": [], "tie_break": False}
    if len(met) >= 3:
        return result | {"reading": "success"}
    if len(possible) <= 1:
        return result | {"reading": "not_confirmed"}
    if len(possible) > 2 or len(met) < 2:
        return result | {"reading": "pending"}
    # 2 of 4. Blocks 3 and 4 met: one extra block is enough (tie-break, DECISIONS.md D-038).
    extension = [day28_block(n, days, today=today) for n in EXTENSION]
    needed = 1 if met == [3, 4] else 2
    extra_met = sum(b["status"] == "met" for b in extension)
    extra_possible = sum(b["status"] != "missed" for b in extension)
    if extra_met >= needed:
        reading = "success"
    elif extra_possible < needed:
        reading = "not_confirmed"
    else:
        reading = "extension"
    return result | {"extension": extension, "tie_break": needed == 1, "reading": reading}


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


# Support metrics (spec 4.11.3) over the Bahia days `start` to `end`, both included. They inform
# the day 28 verdict and decide nothing (DECISIONS.md D-038, D-041).


def open_to_start(*, start, end) -> dict:
    """Seconds from opening the app to starting an activity, the same Bahia day."""
    events = (
        SessionEvent.objects.annotate(day=TruncDate("started_at"))
        .filter(day__range=(start, end))
        .order_by("started_at", "id")
    )
    opens, gaps, opened = 0, [], None
    for kind, day, started_at in events.values_list("kind", "day", "started_at"):
        if kind == Kind.APP_OPENED:
            opens, opened = opens + 1, (day, started_at)
        elif opened and opened[0] == day:
            gaps.append((started_at - opened[1]).total_seconds())
            opened = None
    return {"opens": opens, "started": len(gaps), "median_seconds": median(gaps) if gaps else None}


def reviews_done(*, start, end) -> dict:
    """Distinct cards rated over the day's capped queue, never the backlog (D-011, D-041)."""
    offered = dict(
        DailyReviewQueue.objects.filter(day__range=(start, end), offered__gt=0).values_list(
            "day", "offered"
        )
    )
    rated = dict(
        ReviewLog.objects.annotate(day=TruncDate("reviewed_at"))
        .filter(day__in=offered)
        .values("day")
        .annotate(cards=Count("flashcard", distinct=True))
        .values_list("day", "cards")
    )
    # A card rated outside the recorded queue cannot make a day more than done.
    days = [(day, min(rated.get(day, 0), cards), cards) for day, cards in sorted(offered.items())]
    total = sum(cards for _, _, cards in days)
    return {"days": days, "fraction": sum(done for _, done, _ in days) / total if total else None}


LATE_AFTER_DAYS = 14


def late_card_accuracy(*, start, end) -> dict:
    """First rating of each card per Bahia day, more than 14 days after its concept's completion.

    A concept is completed when all its subtopics are, on the day of the last one (spec 4.4.6).
    Hard counts as recalled, as in Py-FSRS.
    """
    completed = {}
    for concept in Concept.objects.prefetch_related("subtopics"):
        dates = [s.completed_at for s in concept.subtopics.all()]
        # Subtopics completed before D-041 have no date, so their concept cannot be placed.
        if dates and all(dates):
            completed[concept.id] = timezone.localdate(max(dates))
    logs = (
        ReviewLog.objects.annotate(
            day=TruncDate("reviewed_at"),
            concept=Coalesce("flashcard__concept", "flashcard__subtopic__concept"),
        )
        .filter(day__range=(start, end), concept__in=completed)
        # A same-day repeat comes right after the answer was shown, so it tests no recall.
        .order_by("flashcard_id", "day", "reviewed_at")
        .distinct("flashcard_id", "day")
        .values_list("concept", "day", "rating")
    )
    ratings = Counter(
        rating for concept, day, rating in logs if (day - completed[concept]).days > LATE_AFTER_DAYS
    )
    total = sum(ratings.values())
    recalled = ratings[ReviewLog.Rating.HARD] + ratings[ReviewLog.Rating.GOOD]
    return {
        "ratings": {rating: ratings[rating] for rating in ReviewLog.Rating.values},
        "accuracy": recalled / total if total else None,
    }
