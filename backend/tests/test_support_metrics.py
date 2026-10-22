"""Data for the support metrics of spec 4.11.3 and the metrics themselves (DECISIONS.md D-041).

Written by the agent, outside tests/acceptance/. None of this changes a core rule: completion,
the caps and the queue order are covered by test_completion_rules.py and test_review_scheduling.py.
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from activity.models import SessionEvent
from activity.services import late_card_accuracy, open_to_start, reviews_done
from content.models import DailyReviewQueue, Flashcard
from content.parser import parse_markdown
from content.services import (
    approve_card,
    import_content,
    rate_card,
    review_queue,
    start_fsrs_state,
)
from organization.models import Area, Concept, Subtopic
from organization.services import complete_subtopic, reopen_subtopic
from test_completion_rules import attempt, read_all

pytestmark = pytest.mark.django_db

BAHIA = ZoneInfo("America/Bahia")
NOW = datetime(2026, 11, 3, 10, 0, tzinfo=BAHIA)
Kind = SessionEvent.Kind

DOC = """## Ideia central
Esconder o estado interno.

## Prática
### P1: Qual problema resolve?
Resposta de referência: Evita acesso direto.

## Flashcards
- C1: Frente 1 :: Verso 1
- C2: Frente 2 :: Verso 2
- C3: Frente 3 :: Verso 3
"""


@pytest.fixture
def concept():
    area = Area.objects.create(name="Programação")
    return Concept.objects.create(area=area, name="Orientação a objetos")


def studied(concept, name="Encapsulamento"):
    """A subtopic ready to complete, with its three cards approved."""
    subtopic = Subtopic.objects.create(concept=concept, name=name)
    import_content(subtopic, parse_markdown(DOC))
    read_all(subtopic)
    attempt(subtopic, "right")
    for card in Flashcard.objects.filter(subtopic=subtopic):
        approve_card(card)
    return subtopic


def completed_on(subtopic, day):
    complete_subtopic(subtopic)
    Subtopic.objects.filter(pk=subtopic.pk).update(
        completed_at=datetime.combine(day, datetime.min.time(), BAHIA).replace(hour=9)
    )


# Completion date


def test_confirming_completion_records_when_and_reopening_clears_it(concept):
    subtopic = studied(concept)
    assert subtopic.completed_at is None

    complete_subtopic(subtopic)
    first = Subtopic.objects.get(pk=subtopic.pk).completed_at
    assert first is not None and subtopic.completed_at == first

    reopen_subtopic(subtopic)
    assert Subtopic.objects.get(pk=subtopic.pk).completed_at is None

    complete_subtopic(subtopic)
    assert Subtopic.objects.get(pk=subtopic.pk).completed_at > first


# The day's queue


def test_building_the_queue_records_how_many_cards_the_day_offered(concept):
    studied(concept)

    queue = review_queue(now=NOW)

    assert len(queue) == 3
    assert DailyReviewQueue.objects.get(day=NOW.date()).offered == 3


def test_rating_a_card_keeps_the_days_queue_and_a_bigger_queue_replaces_it(concept):
    studied(concept)
    first = review_queue(now=NOW)[0]
    rate_card(first, "good", now=NOW, enable_fuzzing=False)

    review_queue(now=NOW + timedelta(minutes=1))
    assert DailyReviewQueue.objects.get(day=NOW.date()).offered == 3

    studied(concept, name="Herança")
    review_queue(now=NOW + timedelta(minutes=2))
    # The new card cap of 5 stops the six new cards at five.
    assert DailyReviewQueue.objects.get(day=NOW.date()).offered == 5


def test_each_bahia_day_gets_its_own_queue_row(concept):
    studied(concept)
    late = datetime(2026, 11, 3, 23, 30, tzinfo=BAHIA)  # 02:30 UTC on 11-04

    review_queue(now=late)

    assert list(DailyReviewQueue.objects.values_list("day", flat=True)) == [date(2026, 11, 3)]


def test_fraction_of_the_days_reviews_done_reads_the_capped_queue(concept):
    studied(concept)
    cards = review_queue(now=NOW)
    for card in cards[:2]:
        rate_card(card, "again", now=NOW, enable_fuzzing=False)
        rate_card(card, "good", now=NOW + timedelta(minutes=5), enable_fuzzing=False)
    DailyReviewQueue.objects.create(day=date(2026, 11, 4), offered=4)
    DailyReviewQueue.objects.create(day=date(2026, 11, 5), offered=0)

    metric = reviews_done(start=date(2026, 11, 1), end=date(2026, 11, 30))

    # Two distinct cards of three, then a day offered and not touched; an empty day is no day.
    assert metric["days"] == [(date(2026, 11, 3), 2, 3), (date(2026, 11, 4), 0, 4)]
    assert metric["fraction"] == pytest.approx(2 / 7)
    assert reviews_done(start=date(2026, 12, 1), end=date(2026, 12, 2))["fraction"] is None


# Accuracy on cards from concepts completed more than 14 days earlier


def rate_on(concept, day, rating):
    card = Flashcard.objects.filter(subtopic__concept=concept).first()
    at = datetime.combine(day, datetime.min.time(), BAHIA).replace(hour=10)
    rate_card(card, rating, now=at, enable_fuzzing=False)


def test_late_accuracy_counts_only_reviews_more_than_14_days_after_the_concept(concept):
    completed_on(studied(concept), date(2026, 10, 18))
    rate_on(concept, date(2026, 11, 1), "again")  # 14 days later: not yet
    rate_on(concept, date(2026, 11, 2), "good")
    rate_on(concept, date(2026, 11, 3), "hard")
    rate_on(concept, date(2026, 11, 4), "again")

    metric = late_card_accuracy(start=date(2026, 10, 17), end=date(2026, 11, 13))

    assert metric["ratings"] == {"again": 1, "hard": 1, "good": 1}
    assert metric["accuracy"] == pytest.approx(2 / 3)


def test_late_accuracy_takes_only_the_first_rating_of_a_card_each_day(concept):
    completed_on(studied(concept), date(2026, 10, 18))
    forgotten, known = Flashcard.objects.filter(subtopic__concept=concept)[:2]
    at = datetime(2026, 11, 5, 10, 0, tzinfo=BAHIA)
    rate_card(forgotten, "again", now=at, enable_fuzzing=False)
    rate_card(forgotten, "good", now=at + timedelta(minutes=10), enable_fuzzing=False)
    rate_card(known, "good", now=at, enable_fuzzing=False)
    rate_card(forgotten, "good", now=at + timedelta(days=1), enable_fuzzing=False)

    metric = late_card_accuracy(start=date(2026, 10, 17), end=date(2026, 11, 13))

    assert metric["ratings"] == {"again": 1, "hard": 0, "good": 2}


def test_late_accuracy_dates_a_concept_by_its_last_subtopic_and_skips_unfinished_ones(concept):
    completed_on(studied(concept), date(2026, 10, 18))
    completed_on(studied(concept, name="Herança"), date(2026, 10, 25))
    unfinished = Concept.objects.create(area=concept.area, name="Testes")
    completed_on(studied(unfinished), date(2026, 10, 18))
    studied(unfinished, name="Mocks")
    rate_on(concept, date(2026, 11, 2), "good")  # 15 days after the first, 8 after the last
    rate_on(unfinished, date(2026, 11, 12), "good")

    metric = late_card_accuracy(start=date(2026, 10, 17), end=date(2026, 11, 13))

    assert metric == {"ratings": {"again": 0, "hard": 0, "good": 0}, "accuracy": None}


def test_a_subtopic_completed_before_the_date_was_kept_leaves_its_concept_out(concept):
    subtopic = studied(concept)
    complete_subtopic(subtopic)
    Subtopic.objects.filter(pk=subtopic.pk).update(completed_at=None)
    rate_on(concept, date(2026, 11, 12), "good")

    assert late_card_accuracy(start=date(2026, 10, 17), end=date(2026, 11, 13))["accuracy"] is None


def test_a_manual_card_on_a_concept_counts_for_that_concept(concept):
    completed_on(studied(concept), date(2026, 10, 18))
    card = Flashcard.objects.create(
        origin=Flashcard.Origin.MANUAL, concept=concept, front="F", back="V", state="active"
    )
    start_fsrs_state(card)
    rate_card(card, "again", now=datetime(2026, 11, 10, 10, tzinfo=BAHIA), enable_fuzzing=False)

    metric = late_card_accuracy(start=date(2026, 10, 17), end=date(2026, 11, 13))
    assert metric["ratings"]["again"] == 1


# Time from opening the app to starting an activity


def event(kind, at, **subjects):
    return SessionEvent.objects.create(kind=kind, started_at=at, **subjects)


def test_open_to_start_takes_the_first_activity_after_each_opening_the_same_day(concept):
    day = datetime(2026, 10, 20, 8, 0, tzinfo=BAHIA)
    event(Kind.APP_OPENED, day)
    event(Kind.REVIEW_SESSION, day + timedelta(seconds=30))
    event(Kind.REVIEW_SESSION, day + timedelta(seconds=90))  # the same visit, not a new start
    event(Kind.APP_OPENED, day + timedelta(hours=2))
    event(Kind.APP_OPENED, day + timedelta(hours=3))
    event(Kind.REVIEW_SESSION, day + timedelta(hours=3, seconds=120))
    event(Kind.APP_OPENED, day + timedelta(hours=15))  # 23:00, and nothing until the next day
    event(Kind.REVIEW_SESSION, day + timedelta(hours=25))

    metric = open_to_start(start=date(2026, 10, 17), end=date(2026, 11, 13))

    assert metric == {"opens": 4, "started": 2, "median_seconds": 75.0}


def test_open_to_start_without_openings_has_no_median():
    assert open_to_start(start=date(2026, 10, 17), end=date(2026, 11, 13)) == {
        "opens": 0,
        "started": 0,
        "median_seconds": None,
    }
