"""Re-import of a parsed document into a subtopic. Identity follows the labels (spec 4.2.6)."""

from collections import defaultdict
from datetime import UTC, datetime, time, timedelta

import fsrs
from django.db import transaction
from django.db.models import Min
from django.utils import timezone
from organization.models import Settings

from .models import Block, Content, Flashcard, PracticeQuestion, ReviewLog
from .parser import ParsedContent


@transaction.atomic
def import_content(subtopic, parsed: ParsedContent) -> None:
    if parsed.errors:
        raise ValueError("; ".join(parsed.errors))
    _save_content(subtopic, parsed)
    _sync_questions(subtopic, parsed)
    _sync_cards(subtopic, parsed)
    if parsed.level is not None:
        subtopic.level = parsed.level
        subtopic.save(update_fields=["level"])


def _save_content(subtopic, parsed):
    content, _ = Content.objects.update_or_create(
        subtopic=subtopic,
        defaults={
            "raw_markdown": parsed.raw,
            "state": parsed.state,
            "generated_by": parsed.generated_by,
        },
    )
    # A block with identical kind, heading and body keeps its read mark (DECISIONS.md D-015).
    read = defaultdict(list)
    for old in content.blocks.exclude(read_at=None):
        read[(old.kind, old.heading, old.body)].append(old.read_at)
    content.blocks.all().delete()
    blocks = []
    for order, block in enumerate(parsed.blocks):
        marks = read[(block.kind, block.heading, block.body)]
        blocks.append(
            Block(
                content=content,
                order=order,
                kind=block.kind,
                heading=block.heading,
                body=block.body,
                read_at=marks.pop() if marks else None,
            )
        )
    Block.objects.bulk_create(blocks)


def _sync_questions(subtopic, parsed):
    existing = {q.label: q for q in subtopic.questions.all()}
    for item in parsed.questions:
        values = {"prompt": item.prompt, "reference_answer": item.reference_answer or ""}
        PracticeQuestion.objects.update_or_create(
            subtopic=subtopic, label=item.label, defaults={**values, "archived": False}
        )
    kept = {item.label for item in parsed.questions}
    for label, question in existing.items():
        if label not in kept and not question.archived:
            question.archived = True
            question.save(update_fields=["archived"])


def _sync_cards(subtopic, parsed):
    existing = {c.label: c for c in subtopic.flashcards.all()}
    for item in parsed.cards:
        card = existing.get(item.label)
        if card is None:
            card = Flashcard.objects.create(
                subtopic=subtopic, label=item.label, front=item.front, back=item.back
            )
            start_fsrs_state(card)
            continue
        card.front, card.back = item.front, item.back
        if card.state == Flashcard.State.SUSPENDED:
            card.state = card.state_before_suspension or Flashcard.State.PENDING
            card.state_before_suspension = ""
        card.save()
    kept = {item.label for item in parsed.cards}
    for label, card in existing.items():
        if label not in kept and card.state != Flashcard.State.SUSPENDED:
            # A rejected label that leaves and comes back starts over as pending (spec 4.3.4).
            rejected = card.state == Flashcard.State.REJECTED
            card.state_before_suspension = Flashcard.State.PENDING if rejected else card.state
            card.state = Flashcard.State.SUSPENDED
            card.save()


def approve_card(card) -> None:
    """Pending becomes active and new; the new card cap applies to it (spec 4.3.3)."""
    _decide(card, Flashcard.State.ACTIVE)


def reject_card(card) -> None:
    _decide(card, Flashcard.State.REJECTED)


@transaction.atomic
def create_manual_card(*, front, back, subtopic=None, concept=None) -> Flashcard:
    """On a subtopic or on a concept, never both; Diogo's own, so active (spec 4.3.5, Q6)."""
    if (subtopic is None) == (concept is None):
        raise ValueError("Escolha um subtema ou um conceito, não os dois.")
    card = Flashcard.objects.create(
        origin=Flashcard.Origin.MANUAL,
        subtopic=subtopic,
        concept=concept,
        front=front,
        back=back,
        state=Flashcard.State.ACTIVE,
    )
    start_fsrs_state(card)
    return card


def _decide(card, state):
    # One card at a time, and only a pending one: there is no "approve all" (spec 4.3.2).
    if card.state != Flashcard.State.PENDING:
        raise ValueError(f"O cartão {card.label} não está pendente")
    card.state = state
    card.save(update_fields=["state"])


# Review scheduling (spec 4.6, DECISIONS.md D-011, D-018 and D-022).

FSRS_RATINGS = {
    ReviewLog.Rating.AGAIN: fsrs.Rating.Again,
    ReviewLog.Rating.HARD: fsrs.Rating.Hard,
    ReviewLog.Rating.GOOD: fsrs.Rating.Good,
}


def start_fsrs_state(card) -> None:
    """Every card starts as a new Py-FSRS card keyed by its pk, whatever its approval state."""
    _store_fsrs_state(card, fsrs.Card(card_id=card.pk, due=_utc(None)))


@transaction.atomic
def rate_card(card, rating, *, now=None, enable_fuzzing=True) -> ReviewLog:
    """Again, Hard or Good through Py-FSRS; there is no Easy (spec 4.6.2)."""
    if card.state != Flashcard.State.ACTIVE:
        raise ValueError(f"O cartão {card} não está ativo")
    if rating not in ReviewLog.Rating.values:
        raise ValueError(f"Avaliação inválida: {rating}")
    rating = ReviewLog.Rating(rating)
    reviewed_at = _utc(now)
    fsrs_card, fsrs_log = _scheduler(enable_fuzzing).review_card(
        fsrs.Card.from_dict(card.fsrs_card), FSRS_RATINGS[rating], review_datetime=reviewed_at
    )
    _store_fsrs_state(card, fsrs_card)
    return ReviewLog.objects.create(
        flashcard=card, rating=rating, reviewed_at=reviewed_at, fsrs_log=fsrs_log.to_dict()
    )


def review_queue(*, now=None, cap=None) -> list[Flashcard]:
    """Today's cards: same-day repeats first, then new cards, then due cards.

    `cap` lowers the review cap for the day, as the return session does (spec 4.7).
    """
    repeats, picks = _today(now, cap)
    return repeats + picks


def reviews_today(*, now=None, cap=None) -> int:
    """The home screen's N: cards still to see today, never same-day repeats (D-022)."""
    return len(_today(now, cap)[1])


def _today(now, cap):
    now = _utc(now)
    start = timezone.make_aware(datetime.combine(timezone.localdate(now), time.min))
    end = start + timedelta(days=1)
    settings = Settings.load()
    active = Flashcard.objects.filter(state=Flashcard.State.ACTIVE)

    logs_today = ReviewLog.objects.filter(reviewed_at__gte=start, reviewed_at__lt=end)
    seen_today = set(logs_today.values_list("flashcard_id", flat=True))
    introduced_today = (
        ReviewLog.objects.values("flashcard_id")
        .annotate(first=Min("reviewed_at"))
        .filter(first__gte=start, first__lt=end)
        .count()
    )
    # The review cap counts distinct cards per Bahia day (Q14); new cards take slots first.
    review_cap = settings.review_cap if cap is None else min(cap, settings.review_cap)
    free = max(review_cap - len(seen_today), 0)
    new_slots = min(max(settings.new_card_cap - introduced_today, 0), free)
    new = list(active.filter(reviews__isnull=True).order_by("id")[:new_slots])

    due = active.filter(reviews__isnull=False, due__lt=end).exclude(id__in=seen_today).distinct()
    scheduler = _scheduler()

    def retrievability(card):
        return scheduler.get_card_retrievability(fsrs.Card.from_dict(card.fsrs_card), now)

    # Overflow stays due with its stored date untouched and competes again tomorrow (D-011).
    due = sorted(due, key=lambda card: (retrievability(card), card.id))[: free - len(new)]
    repeats = list(active.filter(id__in=seen_today, due__lte=now).order_by("due", "id"))
    return repeats, new + due


def _scheduler(enable_fuzzing=True):
    return fsrs.Scheduler(
        desired_retention=Settings.load().desired_retention, enable_fuzzing=enable_fuzzing
    )


def _store_fsrs_state(card, fsrs_card):
    # The only writer of `fsrs_card` and `due`, so the two never drift apart (D-018).
    card.fsrs_card = fsrs_card.to_dict()
    card.due = fsrs_card.due
    card.save(update_fields=["fsrs_card", "due"])


def _utc(now):
    # Py-FSRS refuses datetimes that are not in UTC.
    return (now or timezone.now()).astimezone(UTC)
