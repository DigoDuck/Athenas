"""Re-import of a parsed document into a subtopic. Identity follows the labels (spec 4.2.6)."""

from django.db import transaction

from .models import Flashcard, PracticeQuestion
from .parser import ParsedContent


@transaction.atomic
def import_content(subtopic, parsed: ParsedContent) -> None:
    if parsed.errors:
        raise ValueError("; ".join(parsed.errors))
    _sync_questions(subtopic, parsed)
    _sync_cards(subtopic, parsed)


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
    suspendable = (Flashcard.State.PENDING, Flashcard.State.ACTIVE)
    for label, card in existing.items():
        if label not in kept and card.state in suspendable:
            card.state_before_suspension, card.state = card.state, Flashcard.State.SUSPENDED
            card.save()
