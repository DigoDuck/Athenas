"""Scenarios 12 to 14 and 51 of the home slice (S6): the home screen and the return session.

Written by the agent at Diogo's request (S6 thread); `tests/acceptance/` stays his. 51 is the new
scenario docs/plan.md names for S6. The rules the spec leaves open are in DECISIONS.md D-026.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from activity.models import SessionEvent
from activity.services import complete_activity, in_return_session, open_home, start_activity
from content.models import Flashcard
from content.parser import parse_markdown
from content.services import approve_card, import_content, rate_card
from django.utils import timezone
from organization.models import Area, Concept, Settings, Step, Subtopic, Track

pytestmark = pytest.mark.django_db

Kind = SessionEvent.Kind
BAHIA = ZoneInfo("America/Bahia")
MONDAY = datetime(2026, 11, 2, 20, 0, tzinfo=BAHIA)
THURSDAY = datetime(2026, 11, 5, 9, 0, tzinfo=BAHIA)
FRIDAY = datetime(2026, 11, 6, 9, 0, tzinfo=BAHIA)
DOC = "## Objetivo\nA.\n\n## Ideia central\nB.\n\n## Flashcards\n{cards}\n"


@pytest.fixture
def subtopic():
    area = Area.objects.create(name="Programação")
    concept = Concept.objects.create(area=area, name="Orientação a objetos")
    subtopic = Subtopic.objects.create(concept=concept, name="Encapsulamento")
    cards = "\n".join(f"- C{n}: Frente {n} :: Verso {n}" for n in range(1, 11))
    import_content(subtopic, parse_markdown(DOC.format(cards=cards)))
    for card in Flashcard.objects.all():
        approve_card(card)
    # Ten new cards with room for all of them, so only a return session can hold N at 5.
    settings = Settings.load()
    settings.new_card_cap = 10
    settings.save()
    return subtopic


def session_at(when, kind=Kind.READING, subtopic=None, completed=True):
    """An activity finished (or abandoned) at a given moment, as the measurement sees it."""
    subjects = {"subtopic": subtopic, "block_order": 0} if kind == Kind.READING else {}
    event = start_activity(kind, **subjects)
    if completed:
        complete_activity(event)
    finished = when if completed else None
    SessionEvent.objects.filter(pk=event.pk).update(
        started_at=when, ended_at=finished, completed_at=finished
    )
    return event


def test_12_last_session_on_monday_opening_on_friday_starts_a_return_session(subtopic):
    session_at(MONDAY, subtopic=subtopic)
    Track.objects.create(name="Back-end").steps.create(concept=subtopic.concept)

    home = open_home(now=FRIDAY)

    assert home["return_session"] is True
    assert home["reviews_today"] == 5
    assert home["last_stop"]["subtopic"] == subtopic.pk
    # Only the point where Diogo stopped and the reviews; nothing else competes for attention.
    assert home["next_steps"] == []


def test_13_last_session_on_monday_opening_on_thursday_is_not_a_return_session(subtopic):
    session_at(MONDAY, subtopic=subtopic)

    home = open_home(now=THURSDAY)

    assert home["return_session"] is False
    assert home["reviews_today"] == 10


def test_14_reviews_done_in_the_return_session_count_toward_that_days_cap(subtopic):
    session_at(MONDAY, subtopic=subtopic)
    settings = Settings.load()
    settings.review_cap = 8
    settings.save()

    cards = list(Flashcard.objects.order_by("id"))
    rate_card(cards[0], "good", now=FRIDAY, enable_fuzzing=False)
    session_at(FRIDAY, kind=Kind.REVIEW_SESSION)
    # One card rated, and its completed review event, do not end the return session.
    assert in_return_session(now=FRIDAY) is True
    assert open_home(now=FRIDAY)["reviews_today"] == 4

    for card in cards[1:5]:
        rate_card(card, "good", now=FRIDAY, enable_fuzzing=False)
    later = FRIDAY + timedelta(hours=1)

    # After 5 reviews the normal cap of 8 applies, and the 5 cards already seen leave 3.
    assert in_return_session(now=later) is False
    assert open_home(now=later)["reviews_today"] == 3


def test_14_another_activity_completed_today_ends_the_return_session(subtopic):
    session_at(MONDAY, subtopic=subtopic)
    session_at(FRIDAY, subtopic=subtopic)

    assert in_return_session(now=FRIDAY + timedelta(minutes=5)) is False


def test_15_an_abandoned_activity_does_not_end_the_absence(subtopic):
    session_at(MONDAY, subtopic=subtopic)
    session_at(MONDAY + timedelta(days=2), subtopic=subtopic, completed=False)

    assert in_return_session(now=FRIDAY) is True


def test_no_return_session_before_the_first_session(subtopic):
    assert in_return_session(now=FRIDAY) is False


def test_51_each_load_of_the_home_screen_records_app_opened(subtopic, client):
    client.post("/api/home/")
    client.post("/api/home/")

    opened = SessionEvent.objects.filter(kind=Kind.APP_OPENED)
    assert opened.count() == 2
    # Opening the app is never a session, so it cannot end an absence either (D-020).
    assert not opened.exclude(completed_at=None).exists()


def test_51_opening_the_app_does_not_count_as_a_session(subtopic):
    session_at(MONDAY, subtopic=subtopic)
    session_at(MONDAY + timedelta(days=2), kind=Kind.APP_OPENED, completed=False)

    assert in_return_session(now=FRIDAY) is True


def test_the_review_screen_gets_at_most_5_cards_in_a_return_session(subtopic, client):
    session_at(timezone.now() - timedelta(days=4), subtopic=subtopic)

    today = client.get("/api/reviews/today/").json()

    assert today["count"] == 5
    assert len(today["cards"]) == 5


def test_home_leads_with_the_last_block_opened_and_each_tracks_next_step(subtopic, client):
    other = Subtopic.objects.create(concept=subtopic.concept, name="Herança")
    start_activity(Kind.READING, subtopic=subtopic, block_order=0)
    start_activity(Kind.READING, subtopic=subtopic, block_order=1)
    track = Track.objects.create(name="Back-end")
    Step.objects.create(track=track, concept=subtopic.concept)
    Track.objects.create(name="Vazia")
    subtopic.study_status = Subtopic.StudyStatus.COMPLETED
    subtopic.save()

    home = client.post("/api/home/").json()

    assert home["last_stop"] == {
        "subtopic": subtopic.pk,
        "subtopic_name": "Encapsulamento",
        "concept_name": "Orientação a objetos",
        "block_heading": "Ideia central",
    }
    assert home["next_steps"] == [
        {
            "track_name": "Back-end",
            "concept_name": "Orientação a objetos",
            "subtopic": other.pk,
            "subtopic_name": "Herança",
        }
    ]
