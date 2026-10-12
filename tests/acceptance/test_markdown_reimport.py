"""Acceptance scenarios for re-importing Markdown into a subtopic (spec 4.2 rule 6 and section 8).

Scenario numbers match section 8 of docs/spec.md. Identity follows the `P` and `C` labels.
"""

import pytest
from content.models import Attempt, Flashcard, PracticeQuestion, ReviewLog
from content.parser import parse_markdown
from content.services import import_content
from organization.models import Area, Concept, Subtopic

pytestmark = pytest.mark.django_db


@pytest.fixture
def subtopic():
    area = Area.objects.create(name="Programação")
    concept = Concept.objects.create(area=area, name="Orientação a objetos")
    return Subtopic.objects.create(concept=concept, name="Encapsulamento")


def doc(questions=(), cards=()):
    """Build a document from (label, text, answer) questions and (label, front, back) cards."""
    parts = ["## Ideia central\nEsconder o estado interno."]
    if questions:
        lines = ["## Prática"]
        for label, prompt, answer in questions:
            lines += [f"### {label}: {prompt}", f"Resposta de referência: {answer}"]
        parts.append("\n".join(lines))
    if cards:
        lines = ["## Flashcards"]
        lines += [f"- {label}: {front} :: {back}" for label, front, back in cards]
        parts.append("\n".join(lines))
    return "\n\n".join(parts) + "\n"


def run_import(subtopic, **kwargs):
    import_content(subtopic, parse_markdown(doc(**kwargs)))


def test_30_reimport_with_changed_text_under_p1_keeps_the_attempts_of_p1(subtopic):
    run_import(subtopic, questions=[("P1", "Pergunta antiga?", "Resposta antiga.")])
    question = PracticeQuestion.objects.get(subtopic=subtopic, label="P1")
    Attempt.objects.create(
        subtopic=subtopic,
        kind=Attempt.Kind.QUESTION,
        question=question,
        text="Minha resposta",
        self_assessment=Attempt.SelfAssessment.PARTIAL,
    )

    run_import(subtopic, questions=[("P1", "Pergunta nova?", "Resposta nova.")])

    updated = PracticeQuestion.objects.get(subtopic=subtopic, label="P1")
    assert updated.pk == question.pk
    assert updated.prompt == "Pergunta nova?"
    assert updated.reference_answer == "Resposta nova."
    assert updated.attempts.count() == 1


def test_31_reimport_with_changed_text_under_c1_keeps_the_review_history_of_c1(subtopic):
    run_import(subtopic, cards=[("C1", "Frente antiga", "Verso antigo")])
    card = Flashcard.objects.get(subtopic=subtopic, label="C1")
    card.state = Flashcard.State.ACTIVE
    card.save()
    ReviewLog.objects.create(flashcard=card, rating=ReviewLog.Rating.GOOD)

    run_import(subtopic, cards=[("C1", "Frente nova", "Verso novo")])

    updated = Flashcard.objects.get(subtopic=subtopic, label="C1")
    assert updated.pk == card.pk
    assert updated.front == "Frente nova"
    assert updated.back == "Verso novo"
    assert updated.state == Flashcard.State.ACTIVE
    assert updated.reviews.count() == 1


def test_32_reimport_without_p2_archives_p2_and_keeps_its_attempts(subtopic):
    run_import(
        subtopic,
        questions=[("P1", "Primeira?", "Sim."), ("P2", "Segunda?", "Também.")],
    )
    p2 = PracticeQuestion.objects.get(subtopic=subtopic, label="P2")
    Attempt.objects.create(
        subtopic=subtopic,
        kind=Attempt.Kind.QUESTION,
        question=p2,
        text="Minha resposta",
        self_assessment=Attempt.SelfAssessment.RIGHT,
    )

    run_import(subtopic, questions=[("P1", "Primeira?", "Sim.")])

    p2.refresh_from_db()
    assert p2.archived is True
    assert p2.attempts.count() == 1
    assert PracticeQuestion.objects.get(subtopic=subtopic, label="P1").archived is False


def test_33_reimport_without_c2_suspends_c2(subtopic):
    run_import(subtopic, cards=[("C1", "Um", "Um."), ("C2", "Dois", "Dois.")])

    run_import(subtopic, cards=[("C1", "Um", "Um.")])

    assert Flashcard.objects.get(subtopic=subtopic, label="C2").state == Flashcard.State.SUSPENDED
    assert Flashcard.objects.get(subtopic=subtopic, label="C1").state == Flashcard.State.PENDING


def test_34_c2_back_restores_it_with_its_review_history_in_the_state_it_had(subtopic):
    run_import(subtopic, cards=[("C1", "Um", "Um."), ("C2", "Dois", "Dois.")])
    card = Flashcard.objects.get(subtopic=subtopic, label="C2")
    card.state = Flashcard.State.ACTIVE
    card.save()
    ReviewLog.objects.create(flashcard=card, rating=ReviewLog.Rating.HARD)
    run_import(subtopic, cards=[("C1", "Um", "Um.")])

    run_import(subtopic, cards=[("C1", "Um", "Um."), ("C2", "Dois", "Dois.")])

    restored = Flashcard.objects.get(subtopic=subtopic, label="C2")
    assert restored.pk == card.pk
    assert restored.state == Flashcard.State.ACTIVE
    assert restored.reviews.count() == 1


def test_34_a_pending_card_that_comes_back_is_pending_again(subtopic):
    run_import(subtopic, cards=[("C2", "Dois", "Dois.")])
    run_import(subtopic)

    run_import(subtopic, cards=[("C2", "Dois", "Dois.")])

    assert Flashcard.objects.get(subtopic=subtopic, label="C2").state == Flashcard.State.PENDING


def test_34_p2_back_restores_the_archived_question_with_its_attempts(subtopic):
    run_import(subtopic, questions=[("P2", "Segunda?", "Também.")])
    p2 = PracticeQuestion.objects.get(subtopic=subtopic, label="P2")
    Attempt.objects.create(
        subtopic=subtopic,
        kind=Attempt.Kind.QUESTION,
        question=p2,
        text="Minha resposta",
        self_assessment=Attempt.SelfAssessment.WRONG,
    )
    run_import(subtopic)

    run_import(subtopic, questions=[("P2", "Segunda?", "Também.")])

    p2.refresh_from_db()
    assert p2.archived is False
    assert p2.attempts.count() == 1


def test_36_a_document_with_duplicate_labels_is_not_saved(subtopic):
    parsed = parse_markdown(doc(cards=[("C1", "Um", "Um."), ("C1", "Outro", "Outro.")]))

    with pytest.raises(ValueError, match="C1"):
        import_content(subtopic, parsed)

    assert Flashcard.objects.count() == 0


def test_35_new_c3_on_reimport_enters_as_pending(subtopic):
    run_import(subtopic, cards=[("C1", "Um", "Um.")])

    run_import(subtopic, cards=[("C1", "Um", "Um."), ("C3", "Três", "Três.")])

    assert Flashcard.objects.get(subtopic=subtopic, label="C3").state == Flashcard.State.PENDING
