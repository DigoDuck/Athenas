"""Who wrote a subtopic's text, from the frontmatter `origem` (DECISIONS.md D-032).

Written by the agent; `tests/acceptance/` stays Diogo's.
"""

import importlib

import pytest
from content.models import Content
from content.parser import parse_markdown
from django.apps import apps
from organization.models import Area, Concept, Subtopic

GENERATED = (
    "---\n"
    "area: Programação\n"
    "conceito: Orientação a objetos\n"
    "subtema: Encapsulamento\n"
    "nivel: iniciante\n"
    "origem: Claude\n"
    "---\n\n"
    "## Ideia central\nEsconder o estado interno.\n"
    "## Prática\n### P1: O que ele esconde?\nResposta de referência: O estado interno.\n"
    "## Flashcards\n- C1: O que o encapsulamento esconde? :: O estado interno.\n"
)
OWN = GENERATED.replace("origem: Claude\n", "")


def test_origem_is_read_lowercased_and_empty_when_absent():
    assert parse_markdown(GENERATED).generated_by == "claude"
    assert parse_markdown(OWN).generated_by == ""


def test_a_long_origem_is_cut_with_a_warning_never_dropped():
    parsed = parse_markdown(GENERATED.replace("origem: Claude", "origem: " + "x" * 40))

    assert parsed.generated_by == "x" * 30
    assert any("Origem" in w for w in parsed.warnings)


@pytest.fixture
def subtopic():
    area = Area.objects.create(name="Programação")
    concept = Concept.objects.create(area=area, name="Orientação a objetos")
    return Subtopic.objects.create(concept=concept, name="Encapsulamento")


def put(client, subtopic, markdown):
    url = f"/api/subtopics/{subtopic.pk}/content/"
    return client.put(url, {"markdown": markdown}, content_type="application/json")


@pytest.mark.django_db
def test_saving_stores_the_origin_and_every_study_screen_gets_it(subtopic, client):
    url = f"/api/subtopics/{subtopic.pk}"
    preview = client.post(
        f"{url}/content/preview/", {"markdown": GENERATED}, content_type="application/json"
    )

    saved = put(client, subtopic, GENERATED)

    assert preview.json()["generated_by"] == "claude"
    assert saved.json()["generated_by"] == "claude"
    assert Content.objects.get().generated_by == "claude"
    assert client.get(f"{url}/reading/").json()["generated_by"] == "claude"
    assert client.get(f"{url}/practice/").json()["generated_by"] == "claude"


@pytest.mark.django_db
def test_saving_without_origem_marks_the_text_as_diogos(subtopic, client):
    put(client, subtopic, GENERATED)

    put(client, subtopic, OWN)

    assert Content.objects.get().generated_by == ""


@pytest.mark.django_db
def test_a_subtopic_without_content_has_no_origin(subtopic, client):
    assert client.get(f"/api/subtopics/{subtopic.pk}/reading/").json()["generated_by"] == ""


@pytest.mark.django_db
def test_the_migration_reads_origem_from_content_saved_before_it(subtopic):
    Content.objects.create(subtopic=subtopic, raw_markdown=GENERATED)
    migration = importlib.import_module("content.migrations.0005_content_generated_by")

    migration.read_origem(apps, None)

    assert Content.objects.get().generated_by == "claude"
