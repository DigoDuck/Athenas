"""Scenarios 15, 19, 49 and 50 of the study reading slice (S1): sessions, status and resume.

Written by the agent at Diogo's request; `tests/acceptance/` stays his. 49 and 50 were proposed in
the S1 thread. The reading rules the spec leaves open are in DECISIONS.md D-020 and D-023.
"""

from datetime import UTC, date, datetime

import pytest
from activity.models import SessionEvent
from activity.services import (
    complete_activity,
    resume_block_order,
    session_days,
    start_activity,
)
from content.models import Block, Content
from content.parser import parse_markdown
from content.services import import_content
from django.utils import timezone
from organization.models import Area, Concept, Subtopic

pytestmark = pytest.mark.django_db

Kind = SessionEvent.Kind
DOC = "## Objetivo\nA.\n\n## Ideia central\nB.\n\n## Explicação\nC.\n\n## Exemplo\nD.\n"


@pytest.fixture
def subtopic():
    area = Area.objects.create(name="Programação")
    concept = Concept.objects.create(area=area, name="Orientação a objetos")
    subtopic = Subtopic.objects.create(concept=concept, name="Encapsulamento")
    import_content(subtopic, parse_markdown(DOC))
    return subtopic


def block(subtopic, order):
    return Block.objects.get(content__subtopic=subtopic, order=order)


def test_15_an_abandoned_activity_does_not_count_as_a_session(subtopic):
    start_activity(Kind.READING, subtopic=subtopic, block_order=0)
    app = start_activity(Kind.APP_OPENED)

    assert session_days() == set()
    with pytest.raises(ValueError):
        complete_activity(app)  # opening the app is never a completed activity
    assert session_days() == set()

    finished = start_activity(Kind.READING, subtopic=subtopic, block_order=1)
    complete_activity(finished)
    assert session_days() == {timezone.localdate()}


def test_a_session_counts_on_its_bahia_day_not_the_utc_day(subtopic):
    event = start_activity(Kind.REVIEW_SESSION)
    # 01:30 UTC on the 16th is 22:30 on the 15th in Bahia (spec 3.3, item 4).
    late = datetime(2026, 10, 16, 1, 30, tzinfo=UTC)
    SessionEvent.objects.filter(pk=event.pk).update(completed_at=late)

    assert session_days() == {date(2026, 10, 15)}


def test_19_opening_the_first_block_moves_the_subtopic_to_in_progress(subtopic):
    assert subtopic.study_status == Subtopic.StudyStatus.NOT_STARTED

    start_activity(Kind.READING, subtopic=subtopic, block_order=0)

    subtopic.refresh_from_db()
    assert subtopic.study_status == Subtopic.StudyStatus.IN_PROGRESS


def test_19_opening_a_block_never_moves_a_completed_subtopic_back(subtopic):
    Subtopic.objects.filter(pk=subtopic.pk).update(study_status=Subtopic.StudyStatus.COMPLETED)

    start_activity(Kind.READING, subtopic=Subtopic.objects.get(pk=subtopic.pk), block_order=2)

    subtopic.refresh_from_db()
    assert subtopic.study_status == Subtopic.StudyStatus.COMPLETED


def test_49_reading_a_block_records_an_event_and_marking_it_read_completes_it(subtopic):
    event = start_activity(Kind.READING, subtopic=subtopic, block_order=2)

    stored = SessionEvent.objects.get(pk=event.pk)
    assert (stored.kind, stored.subtopic_id, stored.block_order) == (Kind.READING, subtopic.pk, 2)
    assert stored.completed_at is None
    assert block(subtopic, 2).read_at is None

    complete_activity(event)

    stored.refresh_from_db()
    assert stored.completed_at is not None
    assert block(subtopic, 2).read_at == stored.completed_at
    assert (
        not Block.objects.filter(content__subtopic=subtopic).exclude(order=2).exclude(read_at=None)
    )
    with pytest.raises(ValueError):
        complete_activity(stored)  # completed once, then never changed (D-020)


def test_49_a_block_re_imported_after_it_was_opened_is_not_marked_read(subtopic):
    event = start_activity(Kind.READING, subtopic=subtopic, block_order=1)
    Content.objects.filter(subtopic=subtopic).update(updated_at=timezone.now())

    complete_activity(event)

    assert event.completed_at is not None  # still a session
    assert not Block.objects.filter(content__subtopic=subtopic).exclude(read_at=None)  # D-023


def test_50_reopening_a_subtopic_resumes_at_the_last_block_opened(subtopic, client):
    assert client.get(f"/api/subtopics/{subtopic.pk}/reading/").json()["resume_block_order"] == 0

    for order in (0, 1, 3, 2):
        start_activity(Kind.READING, subtopic=subtopic, block_order=order)

    assert resume_block_order(subtopic) == 2
    assert client.get(f"/api/subtopics/{subtopic.pk}/reading/").json()["resume_block_order"] == 2


def test_50_resume_stays_inside_the_blocks_after_a_re_import_removes_some(subtopic):
    start_activity(Kind.READING, subtopic=subtopic, block_order=3)

    import_content(subtopic, parse_markdown("## Objetivo\nA.\n\n## Ideia central\nB.\n"))

    assert resume_block_order(subtopic) == 1  # D-017
