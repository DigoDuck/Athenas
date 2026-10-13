"""Re-import of a parsed document into a subtopic. Identity follows the labels (spec 4.2.6)."""

from collections import defaultdict

from django.db import transaction

from .models import Block, Content, Flashcard, PracticeQuestion
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
        subtopic=subtopic, defaults={"raw_markdown": parsed.raw, "state": parsed.state}
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
            Flashcard.objects.create(
                subtopic=subtopic, label=item.label, front=item.front, back=item.back
            )
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


def _decide(card, state):
    # One card at a time, and only a pending one: there is no "approve all" (spec 4.3.2).
    if card.state != Flashcard.State.PENDING:
        raise ValueError(f"O cartão {card.label} não está pendente")
    card.state = state
    card.save(update_fields=["state"])
