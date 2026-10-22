"""Data-loss and safety fixes from the stability audit (DECISIONS.md D-039).

Written by the agent; `tests/acceptance/` stays Diogo's.
"""

import pytest
from content.models import Flashcard
from content.parser import parse_markdown
from content.services import create_manual_card, import_content, rate_card
from organization.models import Area, Concept, Subtopic

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
