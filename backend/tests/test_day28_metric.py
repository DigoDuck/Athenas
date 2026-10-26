"""Day 28 metric (spec 4.11.2, DECISIONS.md D-010, D-029 and D-038).

Written by the agent; `tests/acceptance/` stays Diogo's. The spec has no scenario for the metric,
so these follow the D-010 reading line by line, plus the read-only guarantee of the command.
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from activity.models import SessionEvent
from activity.services import day28_metric
from content.models import DailyReviewQueue
from django.core.management import call_command
from django.db import DatabaseError
from organization.models import Area

BAHIA = ZoneInfo("America/Bahia")
DAY_28 = date(2026, 11, 13)
AFTER_EXTENSION = date(2026, 11, 28)


def block_days(number, count):
    """The first `count` days of a block (block 1 starts on day 1, 2026-10-17)."""
    start = date(2026, 10, 17) + timedelta(days=7 * (number - 1))
    return {start + timedelta(days=n) for n in range(count)}


def use(**counts):
    """Days of use per block, as in use(b1=3, b3=2)."""
    return set().union(*(block_days(int(key[1:]), n) for key, n in counts.items()))


def statuses(metric, key="blocks"):
    return [block["status"] for block in metric[key]]


def test_the_window_is_four_blocks_of_seven_bahia_days_from_day_1():
    blocks = day28_metric(set(), today=DAY_28)["blocks"]
    assert [(b["start"], b["end"]) for b in blocks] == [
        (date(2026, 10, 17), date(2026, 10, 23)),
        (date(2026, 10, 24), date(2026, 10, 30)),
        (date(2026, 10, 31), date(2026, 11, 6)),
        (date(2026, 11, 7), date(2026, 11, 13)),
    ]


def test_three_or_four_blocks_with_three_days_of_use_is_success():
    assert day28_metric(use(b1=3, b2=7, b4=5), today=DAY_28)["reading"] == "success"
    assert day28_metric(use(b1=3, b2=3, b3=3, b4=3), today=DAY_28)["reading"] == "success"


def test_a_block_with_two_days_of_use_does_not_meet_the_bar():
    metric = day28_metric(use(b1=3, b2=3, b3=2, b4=2), today=date(2026, 11, 14))
    assert statuses(metric) == ["met", "met", "missed", "missed"]
    assert metric["reading"] == "extension"


def test_days_outside_the_window_do_not_count():
    before = {date(2026, 10, 14), date(2026, 10, 15), date(2026, 10, 16)}
    metric = day28_metric(before | use(b1=2), today=DAY_28)
    assert metric["blocks"][0]["days"] == sorted(use(b1=2))
    assert metric["reading"] == "not_confirmed"


def test_zero_or_one_block_is_hypothesis_not_confirmed():
    assert day28_metric(set(), today=DAY_28)["reading"] == "not_confirmed"
    assert day28_metric(use(b2=6), today=DAY_28)["reading"] == "not_confirmed"


def test_two_of_four_opens_one_extension_of_blocks_5_and_6():
    metric = day28_metric(use(b1=3, b3=3), today=DAY_28)
    assert metric["reading"] == "extension"
    assert [(b["number"], b["start"], b["end"]) for b in metric["extension"]] == [
        (5, date(2026, 11, 14), date(2026, 11, 20)),
        (6, date(2026, 11, 21), date(2026, 11, 27)),
    ]
    assert not metric["tie_break"]


def test_the_extension_needs_both_blocks():
    both = day28_metric(use(b1=3, b2=3, b5=3, b6=3), today=AFTER_EXTENSION)
    one = day28_metric(use(b1=3, b2=3, b5=3, b6=2), today=AFTER_EXTENSION)
    assert both["reading"] == "success"
    assert one["reading"] == "not_confirmed"


def test_blocks_3_and_4_met_make_one_extension_block_enough():
    one = day28_metric(use(b3=3, b4=3, b6=4), today=AFTER_EXTENSION)
    none = day28_metric(use(b3=3, b4=3, b5=2, b6=2), today=AFTER_EXTENSION)
    assert one["tie_break"] and one["reading"] == "success"
    assert none["tie_break"] and none["reading"] == "not_confirmed"


def test_a_block_is_decided_as_soon_as_the_days_left_cannot_change_it():
    # Block 1, read on its last day: 2 days of use and today still open.
    assert statuses(day28_metric(use(b1=2), today=date(2026, 10, 23)))[0] == "open"
    # Read on its last day with 1 day of use: even using today leaves it at 2.
    assert statuses(day28_metric(use(b1=1), today=date(2026, 10, 23)))[0] == "missed"
    # Met on its third day, before the block ends.
    assert statuses(day28_metric(use(b1=3), today=date(2026, 10, 19)))[0] == "met"


def test_the_reading_waits_while_open_blocks_can_change_it():
    assert day28_metric(use(b1=3, b2=3), today=date(2026, 10, 31))["reading"] == "pending"
    # Three blocks met by day 21: block 4 cannot change it.
    assert day28_metric(use(b1=3, b2=3, b3=3), today=date(2026, 11, 7))["reading"] == "success"
    # Blocks 1 and 2 missed, block 3 met, block 4 still open: at most 2 of 4.
    early = day28_metric(use(b3=3), today=date(2026, 11, 8))
    assert early["reading"] == "pending" and early["extension"] == []


def test_a_past_read_date_ignores_the_days_of_use_after_it():
    metric = day28_metric(use(b1=3, b2=3, b3=3), today=date(2026, 10, 20))
    assert statuses(metric) == ["met", "open", "open", "open"]
    assert metric["blocks"][1]["days"] == []
    assert metric["reading"] == "pending"


def finished_at(when, *, completed=True):
    finished = when if completed else None
    return SessionEvent.objects.create(
        kind=SessionEvent.Kind.REVIEW_SESSION,
        started_at=when,
        ended_at=finished,
        completed_at=finished,
    )


@pytest.mark.django_db
def test_the_command_counts_completed_activities_by_bahia_day(capsys):
    for day in (17, 18, 19):
        finished_at(datetime(2026, 10, day, 10, 0, tzinfo=BAHIA))
        finished_at(datetime(2026, 10, day, 11, 0, tzinfo=BAHIA))
    # 23:30 in Bahia is 02:30 UTC on the 25th: the day of use is the 24th.
    finished_at(datetime(2026, 10, 24, 23, 30, tzinfo=BAHIA))
    finished_at(datetime(2026, 10, 25, 9, 0, tzinfo=BAHIA), completed=False)

    call_command("day28", "--today", "2026-11-13")

    out = capsys.readouterr().out
    assert "| 1 | 2026-10-17 to 2026-10-23 | 3 | 10-17, 10-18, 10-19 | met |" in out
    assert "| 2 | 2026-10-24 to 2026-10-30 | 1 | 10-24 | missed |" in out
    assert "Blocks that met the bar: 1 of 4." in out
    assert "Reading: hypothesis not confirmed." in out
    # D-010's order: the reading comes after the items written by hand.
    assert out.index("Features that shipped") < out.index("Sessions lost") < out.index("Reading:")


@pytest.mark.django_db
def test_the_command_prints_the_support_metrics_over_the_closed_days(capsys):
    opened = datetime(2026, 10, 18, 9, 0, tzinfo=BAHIA)
    SessionEvent.objects.create(kind=SessionEvent.Kind.APP_OPENED, started_at=opened)
    finished_at(opened + timedelta(seconds=30))
    DailyReviewQueue.objects.create(day=date(2026, 10, 18), offered=2)
    # The read date is not over, so its opening stays out.
    SessionEvent.objects.create(
        kind=SessionEvent.Kind.APP_OPENED, started_at=datetime(2026, 10, 19, 9, 0, tzinfo=BAHIA)
    )

    call_command("day28", "--today", "2026-10-19")

    out = capsys.readouterr().out
    assert "Bahia days 2026-10-17 to 2026-10-18." in out
    assert "starting an activity: median 30 s, over 1 of 1 openings." in out
    assert "Reviews done: 0 of 2 cards in the day's queue (0%); days with a queue: 1." in out
    assert "more than 14 days earlier: no such review yet." in out
    assert out.index("Support metrics") < out.index("Features that shipped")


@pytest.mark.django_db
def test_no_support_metrics_before_a_day_of_the_window_closes(capsys):
    call_command("day28", "--today", "2026-10-17")
    assert "no Bahia day of the window has closed yet." in capsys.readouterr().out


@pytest.mark.django_db(transaction=True)
def test_the_command_cannot_write(monkeypatch):
    def write_instead():
        Area.objects.create(name="Programação")

    monkeypatch.setattr("activity.management.commands.day28.session_days", write_instead)
    with pytest.raises(DatabaseError, match="read-only transaction"):
        call_command("day28")
    assert not Area.objects.exists()
