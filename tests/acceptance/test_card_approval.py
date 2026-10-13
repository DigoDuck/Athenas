"""Acceptance scenarios for pending card approval and saving content (spec 4.2.1, 4.2.2, 4.3).

Scenario numbers 40 to 42 match section 8 of docs/spec.md; 43 to 47 were proposed in the card
approval slice and accepted by Diogo; 48 covers DECISIONS.md D-015.
"""

import pytest
from content.models import Content, Flashcard, ReviewLog
from content.parser import parse_markdown
from content.services import approve_card, import_content, reject_card
from django.utils import timezone
from organization.models import Area, Concept, Subtopic

pytestmark = pytest.mark.django_db


@pytest.fixture
def subtopic():
    area = Area.objects.create(name="Programação")
    concept = Concept.objects.create(area=area, name="Orientação a objetos")
    return Subtopic.objects.create(concept=concept, name="Encapsulamento")


def doc(cards=(), idea="Esconder o estado interno.", answer="Evita acesso direto."):
    parts = [
        "---\nnivel: intermediário\n---",
        "Texto solto antes do primeiro título.",
        f"## Ideia central\n{idea}",
        f"## Prática\n### P1: Qual problema resolve?\nResposta de referência: {answer}",
    ]
    if cards:
        lines = ["## Flashcards"]
        lines += [f"- {label}: {front} :: {back}" for label, front, back in cards]
        parts.append("\n".join(lines))
    return "\n\n".join(parts) + "\n"


def run_import(subtopic, **kwargs):
    import_content(subtopic, parse_markdown(doc(**kwargs)))


def card(subtopic, label):
    return Flashcard.objects.get(subtopic=subtopic, label=label)


def test_40_approving_a_pending_card_makes_it_active_and_new(subtopic):
    # The new card cap part of scenario 40 needs the review queue (scheduling slice).
    run_import(subtopic, cards=[("C1", "Frente", "Verso")])

    approve_card(card(subtopic, "C1"))

    approved = card(subtopic, "C1")
    assert approved.state == Flashcard.State.ACTIVE
    assert approved.reviews.count() == 0


def test_41_approving_one_card_leaves_the_others_pending(subtopic, client):
    run_import(subtopic, cards=[("C1", "Um", "Um."), ("C2", "Dois", "Dois.")])

    approve_card(card(subtopic, "C1"))

    assert card(subtopic, "C2").state == Flashcard.State.PENDING
    # The API approves by card id only; there is no collection-level approve.
    response = client.post("/api/flashcards/approve/")
    assert response.status_code in (404, 405)
    assert card(subtopic, "C2").state == Flashcard.State.PENDING


def test_42_a_rejected_card_stays_rejected_when_the_same_markdown_is_imported_again(subtopic):
    run_import(subtopic, cards=[("C1", "Frente", "Verso")])
    reject_card(card(subtopic, "C1"))

    run_import(subtopic, cards=[("C1", "Frente", "Verso")])

    assert card(subtopic, "C1").state == Flashcard.State.REJECTED


def test_43_rejecting_a_pending_card_makes_it_rejected(subtopic):
    run_import(subtopic, cards=[("C1", "Frente", "Verso")])

    reject_card(card(subtopic, "C1"))

    assert card(subtopic, "C1").state == Flashcard.State.REJECTED


def test_44_a_rejected_label_removed_and_added_again_comes_back_pending(subtopic):
    run_import(subtopic, cards=[("C1", "Frente", "Verso")])
    reject_card(card(subtopic, "C1"))
    run_import(subtopic)

    run_import(subtopic, cards=[("C1", "Frente", "Verso")])

    assert card(subtopic, "C1").state == Flashcard.State.PENDING


@pytest.mark.parametrize(
    "state", [Flashcard.State.ACTIVE, Flashcard.State.SUSPENDED, Flashcard.State.REJECTED]
)
@pytest.mark.parametrize("decide", [approve_card, reject_card])
def test_45_only_a_pending_card_can_be_approved_or_rejected(subtopic, state, decide):
    run_import(subtopic, cards=[("C1", "Frente", "Verso")])
    target = card(subtopic, "C1")
    target.state = state
    target.save()
    if state == Flashcard.State.ACTIVE:
        ReviewLog.objects.create(flashcard=target, rating=ReviewLog.Rating.GOOD)

    with pytest.raises(ValueError, match="C1"):
        decide(card(subtopic, "C1"))

    assert card(subtopic, "C1").state == state
    assert card(subtopic, "C1").reviews.count() == (1 if state == Flashcard.State.ACTIVE else 0)


def test_46_saving_keeps_the_raw_markdown_the_blocks_in_order_and_the_state(subtopic):
    text = doc(cards=[("C1", "Frente", "Verso")])

    import_content(subtopic, parse_markdown(text))

    content = Content.objects.get(subtopic=subtopic)
    assert content.raw_markdown == text
    assert content.state == Content.State.READY
    assert [(b.kind, b.heading) for b in content.blocks.order_by("order")] == [
        ("extra", ""),
        ("Ideia central", "Ideia central"),
        ("Prática", "Prática"),
        ("Flashcards", "Flashcards"),
    ]


def test_46_saving_without_ideia_central_keeps_the_content_as_draft(subtopic):
    run_import(subtopic, idea="")

    assert Content.objects.get(subtopic=subtopic).state == Content.State.DRAFT


def test_46_the_frontmatter_nivel_sets_the_subtopic_level(subtopic):
    run_import(subtopic)

    subtopic.refresh_from_db()
    assert subtopic.level == Subtopic.Level.INTERMEDIATE


def test_47_the_preview_saves_nothing(subtopic, client):
    text = doc(cards=[("C1", "Frente", "Verso")])

    response = client.post(
        f"/api/subtopics/{subtopic.pk}/content/preview/", {"markdown": text}, "application/json"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "ready"
    assert [c["label"] for c in body["cards"]] == ["C1"]
    assert not Content.objects.exists()
    assert not Flashcard.objects.exists()
    subtopic.refresh_from_db()
    assert subtopic.level == Subtopic.Level.UNSET


def test_48_reimport_keeps_the_read_mark_only_of_blocks_whose_text_did_not_change(subtopic):
    run_import(subtopic)
    content = Content.objects.get(subtopic=subtopic)
    content.blocks.update(read_at=timezone.now())

    run_import(subtopic, answer="Evita acesso direto ao estado.")

    marks = {b.kind: b.read_at for b in content.blocks.all()}
    assert marks["Ideia central"] is not None
    assert marks["extra"] is not None
    assert marks["Prática"] is None
