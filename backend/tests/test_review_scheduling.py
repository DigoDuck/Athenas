"""Scenarios 1 to 11 and 25 of docs/spec.md section 8: review scheduling and caps (spec 4.6).

Written by the agent at Diogo's request (S4 thread); `tests/acceptance/` stays his. The queue
rules the spec leaves open are in DECISIONS.md D-022.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import fsrs
import pytest
from content.models import Flashcard, ReviewLog
from content.parser import parse_markdown
from content.services import approve_card, import_content, rate_card, review_queue, reviews_today
from organization.models import Area, Concept, Settings, Subtopic

pytestmark = pytest.mark.django_db

BAHIA = ZoneInfo("America/Bahia")
NOW = datetime(2026, 11, 3, 10, 0, tzinfo=BAHIA)


@pytest.fixture
def subtopic():
    area = Area.objects.create(name="Programação")
    concept = Concept.objects.create(area=area, name="Orientação a objetos")
    return Subtopic.objects.create(concept=concept, name="Encapsulamento")


def make_cards(subtopic, count, approve=True):
    lines = "\n".join(f"- C{n}: Frente {n} :: Verso {n}" for n in range(1, count + 1))
    import_content(subtopic, parse_markdown(f"## Ideia central\nX.\n\n## Flashcards\n{lines}\n"))
    cards = list(Flashcard.objects.filter(subtopic=subtopic).order_by("id"))
    if approve:
        for card in cards:
            approve_card(card)
    return cards


def graduate(card, at):
    """Two Good ratings 10 minutes apart take a new card out of learning into review."""
    rate_card(card, "good", now=at, enable_fuzzing=False)
    rate_card(card, "good", now=at + timedelta(minutes=10), enable_fuzzing=False)
    card.refresh_from_db()


def set_caps(review=None, new=None):
    settings = Settings.load()
    if review is not None:
        settings.review_cap = review
    if new is not None:
        settings.new_card_cap = new
    settings.save()


def retrievability(card):
    return fsrs.Scheduler().get_card_retrievability(fsrs.Card.from_dict(card.fsrs_card), NOW)


def test_1_rating_updates_the_card_through_py_fsrs_and_saves_a_review_log(subtopic):
    for rating in ("again", "hard", "good"):
        (card,) = make_cards(Subtopic.objects.create(concept=subtopic.concept, name=rating), 1)
        before = dict(card.fsrs_card)

        log = rate_card(card, rating, now=NOW, enable_fuzzing=False)

        card.refresh_from_db()
        assert card.fsrs_card != before
        assert card.due == fsrs.Card.from_dict(card.fsrs_card).due
        assert log.rating == rating
        assert log.fsrs_log["card_id"] == card.pk


def test_2_there_is_no_easy_rating(subtopic):
    (card,) = make_cards(subtopic, 1)

    with pytest.raises(ValueError):
        rate_card(card, "easy", now=NOW)

    assert "easy" not in ReviewLog.Rating.values
    assert not ReviewLog.objects.exists()


def test_3_with_30_cards_due_and_a_cap_of_20_the_queue_has_20(subtopic):
    for days, card in enumerate(make_cards(subtopic, 30)):
        graduate(card, NOW - timedelta(days=10 + days))

    assert len(review_queue(now=NOW)) == 20


def test_4_the_cards_picked_have_the_lowest_retrievability(subtopic):
    for days, card in enumerate(make_cards(subtopic, 30)):
        graduate(card, NOW - timedelta(days=10 + days))

    picked = {card.id for card in review_queue(now=NOW)}

    values = {card.id: retrievability(card) for card in Flashcard.objects.all()}
    left_out = [value for card_id, value in values.items() if card_id not in picked]
    assert max(values[card_id] for card_id in picked) <= min(left_out)


def test_5_cards_left_out_stay_due_with_their_due_date_unchanged(subtopic):
    for days, card in enumerate(make_cards(subtopic, 30)):
        graduate(card, NOW - timedelta(days=10 + days))
    dues = {card.id: card.due for card in Flashcard.objects.all()}

    picked = {card.id for card in review_queue(now=NOW)}

    left_out = Flashcard.objects.exclude(id__in=picked)
    assert left_out.count() == 10
    assert all(card.due == dues[card.id] for card in left_out)
    next_day = review_queue(now=NOW + timedelta(days=1))
    assert {card.id for card in next_day} <= set(dues)
    assert len(next_day) == 20


def test_6_with_8_new_cards_and_a_cap_of_5_the_queue_introduces_5(subtopic):
    cards = make_cards(subtopic, 8)

    queue = review_queue(now=NOW)

    assert [card.id for card in queue] == [card.id for card in cards[:5]]


def test_7_pending_suspended_and_rejected_cards_never_enter_the_queue(subtopic):
    cards = make_cards(subtopic, 3, approve=False)
    Flashcard.objects.filter(id=cards[1].id).update(state=Flashcard.State.SUSPENDED)
    Flashcard.objects.filter(id=cards[2].id).update(state=Flashcard.State.REJECTED)

    assert review_queue(now=NOW) == []
    assert reviews_today(now=NOW) == 0


def test_8_reviews_today_never_exceeds_the_remaining_cap(subtopic):
    cards = make_cards(subtopic, 5)
    for card in cards[:3]:
        rate_card(card, "again", now=NOW, enable_fuzzing=False)
    set_caps(review=4)

    later = NOW + timedelta(minutes=5)

    # One slot left; the three same-day repeats are in the queue but not in the count.
    assert reviews_today(now=later) == 1
    assert len(review_queue(now=later)) == 4


def test_9_changing_the_review_cap_changes_todays_remaining_count(subtopic):
    cards = make_cards(subtopic, 5)
    for card in cards[:3]:
        rate_card(card, "good", now=NOW, enable_fuzzing=False)

    set_caps(review=4)
    assert reviews_today(now=NOW) == 1

    set_caps(review=20)
    assert reviews_today(now=NOW) == 2


def test_10_a_review_at_22_30_in_bahia_counts_toward_that_bahia_day(subtopic):
    cards = make_cards(subtopic, 2)
    late = datetime(2026, 11, 3, 22, 30, tzinfo=BAHIA)  # 01:30 UTC on Nov 4
    rate_card(cards[0], "good", now=late, enable_fuzzing=False)
    set_caps(review=1)

    assert reviews_today(now=late + timedelta(minutes=20)) == 0
    assert reviews_today(now=datetime(2026, 11, 4, 8, 0, tzinfo=BAHIA)) == 1


def test_11_a_card_failed_and_shown_again_the_same_day_uses_no_other_slot(subtopic):
    cards = make_cards(subtopic, 3)
    rate_card(cards[0], "again", now=NOW, enable_fuzzing=False)
    later = NOW + timedelta(minutes=5)

    queue = review_queue(now=later)
    assert queue[0].id == cards[0].id
    assert reviews_today(now=later) == 2

    rate_card(cards[0], "again", now=later, enable_fuzzing=False)
    assert reviews_today(now=later) == 2


def test_25_completing_a_concept_keeps_its_cards_in_review(subtopic):
    make_cards(subtopic, 1)
    # Concept status is derived from its subtopics (spec 4.4.6): all completed means completed.
    subtopic.study_status = Subtopic.StudyStatus.COMPLETED
    subtopic.save()

    assert len(review_queue(now=NOW)) == 1


def test_40_an_approved_card_is_subject_to_the_new_card_cap(subtopic):
    # The part of scenario 40 that waited for the queue (see test_card_approval.py).
    make_cards(subtopic, 2)
    set_caps(new=1)

    assert len(review_queue(now=NOW)) == 1
