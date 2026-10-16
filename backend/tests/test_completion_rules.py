"""Study status and completion (spec 4.4, 4.5.1, DECISIONS.md D-024).

Scenario numbers 20 to 24 match section 8 of docs/spec.md; the letter suffixes cover D-024.
Written by the agent at Diogo's request, outside tests/acceptance/, so they check the agent's own
reading of the spec.
"""

import pytest
from activity.models import SessionEvent
from activity.services import complete_activity, record_attempt, start_activity
from content.models import Block
from content.parser import parse_markdown
from content.services import import_content
from organization.models import Area, Concept, Step, Subtopic, Track
from organization.services import (
    complete_subtopic,
    completion_suggested,
    concept_status,
    next_step,
    reopen_subtopic,
)

pytestmark = pytest.mark.django_db

Status = Subtopic.StudyStatus
Kind = SessionEvent.Kind

DOC = """## Ideia central
Esconder o estado interno.

## Prática
### P1: Qual problema resolve?
Resposta de referência: Evita acesso direto.
"""


@pytest.fixture
def concept():
    area = Area.objects.create(name="Programação")
    return Concept.objects.create(area=area, name="Orientação a objetos")


@pytest.fixture
def subtopic(concept):
    subtopic = Subtopic.objects.create(concept=concept, name="Encapsulamento")
    import_content(subtopic, parse_markdown(DOC))
    return subtopic


def read_all(subtopic):
    for block in Block.objects.filter(content__subtopic=subtopic):
        complete_activity(start_activity(Kind.READING, subtopic=subtopic, block_order=block.order))
    subtopic.refresh_from_db()


def attempt(subtopic, rating):
    event = start_activity(Kind.EXPLANATION, subtopic=subtopic)
    record_attempt(event, text="Minha explicação.", self_assessment=rating)


def status_of(subtopic):
    subtopic.refresh_from_db()
    return subtopic.study_status


def test_20_the_four_classification_fields_change_independently(subtopic, client):
    url = f"/api/subtopics/{subtopic.pk}/"
    client.patch(url, {"level": "avancado"}, content_type="application/json")
    client.patch(url, {"perceived_difficulty": "hard"}, content_type="application/json")
    client.patch(url, {"review_needed": True}, content_type="application/json")
    assert status_of(subtopic) == Status.NOT_STARTED

    read_all(subtopic)
    attempt(subtopic, "right")
    complete_subtopic(subtopic)

    subtopic.refresh_from_db()
    assert subtopic.study_status == Status.COMPLETED
    assert subtopic.level == "avancado"
    assert subtopic.perceived_difficulty == "hard"
    assert subtopic.review_needed is True


def test_20a_the_api_does_not_change_study_status(subtopic, client):
    response = client.patch(
        f"/api/subtopics/{subtopic.pk}/",
        {"study_status": "completed"},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert status_of(subtopic) == Status.NOT_STARTED


def test_21_all_blocks_read_and_one_partial_attempt_is_suggested_complete(subtopic):
    read_all(subtopic)
    attempt(subtopic, "wrong")
    attempt(subtopic, "partial")

    assert completion_suggested(subtopic)


def test_21a_one_unread_block_is_not_suggested(subtopic):
    read_all(subtopic)
    attempt(subtopic, "right")
    Block.objects.filter(content__subtopic=subtopic, order=0).update(read_at=None)

    assert not completion_suggested(subtopic)


def test_22_all_blocks_read_and_only_wrong_attempts_is_not_suggested(subtopic):
    read_all(subtopic)
    attempt(subtopic, "wrong")
    attempt(subtopic, "wrong")

    assert not completion_suggested(subtopic)


def test_22a_a_subtopic_without_blocks_is_not_suggested(concept):
    empty = Subtopic.objects.create(concept=concept, name="Sem conteúdo")
    attempt(empty, "right")

    assert not completion_suggested(empty)


def test_23_a_suggestion_changes_the_status_only_when_diogo_confirms(subtopic, client):
    read_all(subtopic)
    attempt(subtopic, "right")
    detail = client.get(f"/api/subtopics/{subtopic.pk}/").json()
    assert detail["completion_suggested"] is True
    assert status_of(subtopic) == Status.IN_PROGRESS

    response = client.post(f"/api/subtopics/{subtopic.pk}/complete/")

    assert response.status_code == 200
    assert response.json()["study_status"] == Status.COMPLETED
    assert status_of(subtopic) == Status.COMPLETED


def test_23a_confirming_a_subtopic_that_is_not_suggested_is_refused(subtopic, client):
    read_all(subtopic)

    response = client.post(f"/api/subtopics/{subtopic.pk}/complete/")

    assert response.status_code == 409
    assert status_of(subtopic) == Status.IN_PROGRESS


def test_23a_confirming_twice_is_refused(subtopic, client):
    read_all(subtopic)
    attempt(subtopic, "right")
    client.post(f"/api/subtopics/{subtopic.pk}/complete/")

    assert client.post(f"/api/subtopics/{subtopic.pk}/complete/").status_code == 409


def test_23b_reopening_moves_back_to_in_progress_and_the_concept_too(subtopic, client):
    read_all(subtopic)
    attempt(subtopic, "right")
    complete_subtopic(subtopic)
    assert concept_status(subtopic.concept) == Status.COMPLETED

    response = client.post(f"/api/subtopics/{subtopic.pk}/reopen/")

    assert response.status_code == 200
    assert status_of(subtopic) == Status.IN_PROGRESS
    assert concept_status(subtopic.concept) == Status.IN_PROGRESS


def test_23b_only_a_completed_subtopic_can_be_reopened(subtopic):
    with pytest.raises(ValueError):
        reopen_subtopic(subtopic)
    assert status_of(subtopic) == Status.NOT_STARTED


def test_23c_completing_and_reopening_keep_attempts_and_read_marks(subtopic):
    read_all(subtopic)
    attempt(subtopic, "right")
    complete_subtopic(subtopic)
    reopen_subtopic(subtopic)

    assert subtopic.attempts.count() == 1
    assert not Block.objects.filter(content__subtopic=subtopic, read_at=None).exists()


def test_23c_a_reimport_does_not_change_a_completed_status(subtopic):
    read_all(subtopic)
    attempt(subtopic, "right")
    complete_subtopic(subtopic)

    import_content(subtopic, parse_markdown(DOC.replace("Esconder", "Proteger")))

    assert status_of(subtopic) == Status.COMPLETED


def test_24_a_concept_is_completed_when_all_subtopics_are_and_in_progress_when_some_are(
    subtopic, concept
):
    other = Subtopic.objects.create(concept=concept, name="Herança")
    import_content(other, parse_markdown(DOC))
    read_all(subtopic)
    attempt(subtopic, "right")
    complete_subtopic(subtopic)

    assert concept_status(concept) == Status.IN_PROGRESS

    read_all(other)
    attempt(other, "partial")
    complete_subtopic(other)

    assert concept_status(concept) == Status.COMPLETED


def test_24_a_concept_is_not_started_while_all_subtopics_are(subtopic, concept, client):
    Subtopic.objects.create(concept=concept, name="Herança")

    assert concept_status(concept) == Status.NOT_STARTED
    assert client.get("/api/concepts/").json()[0]["study_status"] == Status.NOT_STARTED


def test_24a_a_concept_without_subtopics_is_not_started(concept):
    assert concept_status(concept) == Status.NOT_STARTED


def test_24b_the_next_step_is_the_first_concept_that_is_not_completed(subtopic, concept, client):
    area = concept.area
    later = Concept.objects.create(area=area, name="Padrões de projeto")
    track = Track.objects.create(name="Back-end")
    first = Step.objects.create(track=track, concept=concept, order=0)
    second = Step.objects.create(track=track, concept=later, order=1)
    assert next_step(track) == first

    read_all(subtopic)
    attempt(subtopic, "right")
    complete_subtopic(subtopic)

    assert next_step(track) == second
    data = client.get("/api/tracks/").json()[0]
    assert data["next_step"] == second.pk
    assert [s["concept_status"] for s in data["steps"]] == [Status.COMPLETED, Status.NOT_STARTED]
