"""Scenarios 36 and 39 of docs/spec.md section 8 through the save endpoint (spec 4.2.7, 4.2.9).

Written by the agent for the D-027 check; `tests/acceptance/` stays Diogo's and covers the parser
and service side of both scenarios.
"""

import pytest
from content.models import Content, Flashcard
from organization.models import Area, Concept, Subtopic

pytestmark = pytest.mark.django_db

OTHER_SUBTOPIC = (
    "---\n"
    "area: Programação\n"
    "conceito: Orientação a objetos\n"
    "subtema: Herança\n"
    "---\n\n"
    "## Ideia central\nEsconder o estado interno.\n"
)


@pytest.fixture
def subtopic():
    area = Area.objects.create(name="Programação")
    concept = Concept.objects.create(area=area, name="Orientação a objetos")
    Subtopic.objects.create(concept=concept, name="Herança")
    return Subtopic.objects.create(concept=concept, name="Encapsulamento")


def send(client, method, url, markdown):
    return getattr(client, method)(url, {"markdown": markdown}, content_type="application/json")


def test_39_frontmatter_naming_another_subtopic_warns_and_saves_into_the_edited_one(
    subtopic, client
):
    url = f"/api/subtopics/{subtopic.pk}/content/"

    preview = send(client, "post", url + "preview/", OTHER_SUBTOPIC).json()
    response = send(client, "put", url, OTHER_SUBTOPIC)

    assert len(preview["warnings"]) == 1
    assert "subtema" in preview["warnings"][0]
    assert response.status_code == 200
    assert Content.objects.get().subtopic == subtopic


def test_36_two_c1_labels_block_the_save_with_a_message_naming_the_label(subtopic, client):
    markdown = "## Flashcards\n- C1: Um :: Um.\n- C1: Outro :: Outro.\n"

    response = send(client, "put", f"/api/subtopics/{subtopic.pk}/content/", markdown)

    assert response.status_code == 400
    assert "C1" in response.json()["errors"][0]
    assert not Content.objects.exists()
    assert not Flashcard.objects.exists()
