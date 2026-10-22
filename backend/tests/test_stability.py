"""Data-loss and safety fixes from the stability audit (DECISIONS.md D-039).

Written by the agent; `tests/acceptance/` stays Diogo's.
"""

import pytest
from content.models import Flashcard
from content.parser import parse_markdown
from content.services import create_manual_card, import_content, rate_card
from organization.models import Area, Concept, Step, Subtopic, Track
from organization.serializers import StepSerializer
from rest_framework.exceptions import ValidationError

pytestmark = pytest.mark.django_db

MARKDOWN = "## Ideia central\nX.\n\n## Flashcards\n- C1: Frente :: Verso\n"


@pytest.fixture
def subtopic():
    area = Area.objects.create(name="Programação")
    concept = Concept.objects.create(area=area, name="Orientação a objetos")
    return Subtopic.objects.create(concept=concept, name="Encapsulamento")


def test_reimport_keeps_manual_cards_on_the_subtopic_active(subtopic):
    import_content(subtopic, parse_markdown(MARKDOWN))
    first = create_manual_card(front="Um", back="Um.", subtopic=subtopic)
    second = create_manual_card(front="Dois", back="Dois.", subtopic=subtopic)
    rate_card(second, "good")

    import_content(subtopic, parse_markdown(MARKDOWN))

    states = set(Flashcard.objects.filter(pk__in=[first.pk, second.pk]).values_list("state"))
    assert states == {(Flashcard.State.ACTIVE,)}
    assert Flashcard.objects.get(label="C1").state == Flashcard.State.PENDING


def test_a_form_post_from_another_site_writes_nothing(subtopic, client):
    import_content(subtopic, parse_markdown(MARKDOWN))
    card = Flashcard.objects.get(label="C1")
    url = f"/api/flashcards/{card.pk}/approve/"

    form = client.post(url, {"x": "1"})
    text = client.post(url, "x", content_type="text/plain")
    card.refresh_from_db()
    assert (form.status_code, text.status_code, card.state) == (415, 415, Flashcard.State.PENDING)

    assert client.post(url, content_type="application/json").status_code == 200


def test_saving_over_content_changed_since_the_editor_opened_answers_409(subtopic, client):
    url = f"/api/subtopics/{subtopic.pk}/content/"
    old = client.put(url, {"markdown": MARKDOWN, "base": None}, "application/json").json()
    newer = MARKDOWN + "\n## Exemplo\nNovo.\n"
    client.put(url, {"markdown": newer, "base": old["raw_markdown"]}, "application/json")

    stale = client.put(url, {"markdown": MARKDOWN, "base": old["raw_markdown"]}, "application/json")
    unseen = client.put(url, {"markdown": MARKDOWN, "base": None}, "application/json")

    assert (stale.status_code, unseen.status_code) == (409, 409)
    assert stale.json()["raw_markdown"] == newer
    assert subtopic.content.raw_markdown == newer
    on_purpose = client.put(url, {"markdown": MARKDOWN, "base": newer}, "application/json")
    assert on_purpose.status_code == 200
    # theme.py sends no base: its own guard decides (DECISIONS.md D-030).
    assert client.put(url, {"markdown": newer}, "application/json").status_code == 200


def test_bad_input_answers_400_not_500(subtopic, client):
    track = Track.objects.create(name="Trilha")
    step = Step.objects.create(track=track, concept=subtopic.concept, order=0)

    cards = client.get("/api/flashcards/?subtopic=undefined")
    move = client.post(f"/api/steps/{step.pk}/move/", ["up"], "application/json")
    assert (cards.status_code, move.status_code) == (400, 400)

    # A double click passes validate() twice; the second insert must not reach the constraint.
    data = {"track": track, "concept": subtopic.concept}
    with pytest.raises(ValidationError):
        StepSerializer().create(data)
