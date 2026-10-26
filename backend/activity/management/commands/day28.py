"""Day 28 metric (spec 4.11.2, DECISIONS.md D-010, D-029 and D-038).

Prints the blocks, the support metrics (D-041) and the reading that applies as Markdown for the
verdict entry. It runs against use mode's real data, so it only reads, inside a read-only
transaction.
"""

from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from activity.services import (
    DAY_1,
    day28_metric,
    late_card_accuracy,
    open_to_start,
    reviews_done,
    session_days,
)

READINGS = {
    "success": "success. Move on to the portfolio phase.",
    "not_confirmed": (
        "hypothesis not confirmed. A written diagnosis from the session event table comes before "
        "any new feature; the next decision is Diogo's."
    ),
    "extension": (
        "2 of 4, neither success nor failure. One single 14-day extension with no new features, "
        "in blocks 5 and 6."
    ),
    "pending": "not decided yet. Blocks that are still open can change it.",
}


def row(block, today):
    days = ", ".join(f"{day:%m-%d}" for day in block["days"]) or "none"
    status = block["status"]
    if status == "open" and block["start"] > today:
        status = "not started"
    return (
        f"| {block['number']} | {block['start']} to {block['end']} | {len(block['days'])} | "
        f"{days} | {status} |"
    )


def support_metrics(metric, today):
    """Spec 4.11.3 over the closed Bahia days of the window, or None before one closes (D-041)."""
    last = (metric["extension"] or metric["blocks"])[-1]["end"]
    # Today is not over, and a day after the window is not part of it.
    end = min(last, today - timedelta(days=1))
    if end < DAY_1:
        return None
    span = {"start": DAY_1, "end": end}
    return {
        "end": end,
        "opening": open_to_start(**span),
        "reviews": reviews_done(**span),
        "accuracy": late_card_accuracy(**span),
    }


def support_lines(support):
    if support is None:
        return ["Support metrics (spec 4.11.3, D-041): no Bahia day of the window has closed yet."]
    opening, reviews, accuracy = support["opening"], support["reviews"], support["accuracy"]
    if opening["median_seconds"] is None:
        opened = f"no opening led to an activity (openings: {opening['opens']})."
    else:
        opened = (
            f"median {opening['median_seconds']:.0f} s; openings followed by one: "
            f"{opening['started']} of {opening['opens']}."
        )
    if reviews["fraction"] is None:
        reviewed = "no day had a review queue."
    else:
        done = sum(day[1] for day in reviews["days"])
        offered = sum(day[2] for day in reviews["days"])
        # Rounded down, so a day with one card left never reads as 100%.
        reviewed = (
            f"{done} of {offered} cards in the day's queue ({done * 100 // offered}%); "
            f"days with a queue: {len(reviews['days'])}."
        )
    ratings = accuracy["ratings"]
    if accuracy["accuracy"] is None:
        recalled = "no such review yet."
    else:
        known, total = ratings["hard"] + ratings["good"], sum(ratings.values())
        recalled = (
            f"{known} of {total} recalled ({known * 100 // total}%); again {ratings['again']}, "
            f"hard {ratings['hard']}, good {ratings['good']}."
        )
    return [
        f"Support metrics (spec 4.11.3, D-041), Bahia days {DAY_1} to {support['end']}. They "
        "decide nothing.",
        "",
        f"- Opening the app to starting an activity: {opened}",
        f"- Reviews done: {reviewed}",
        f"- Cards of concepts completed more than 14 days earlier: {recalled}",
    ]


def report(metric, today, support):
    lines = [
        f"Day 28 metric (D-010), read on {today}.",
        "",
        "| Block | Bahia days | Days of use | Dates | Result |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines += [row(block, today) for block in metric["blocks"] + metric["extension"]]
    met = sum(block["status"] == "met" for block in metric["blocks"])
    lines += ["", f"Blocks that met the bar: {met} of 4."]
    if metric["tie_break"]:
        lines.append("Blocks 3 and 4 met the bar, so one extension block is enough (D-038).")
    # D-010's order: the numbers (blocks, then the support metrics of D-041), the two items the
    # events cannot know, the reading.
    lines += ["", *support_lines(support)]
    lines += [
        "",
        "Features that shipped that month: (write by hand)",
        "Sessions lost to being away from the computer: (write by hand)",
        "",
        f"Reading: {READINGS[metric['reading']]}",
    ]
    return "\n".join(lines)


class Command(BaseCommand):
    help = "Print the day 28 blocks and the D-010 reading. Reads only."

    def add_arguments(self, parser):
        parser.add_argument(
            "--today", type=date.fromisoformat, help="Bahia date to read on (default: today)"
        )

    def handle(self, *args, today=None, **options):
        today = today or timezone.localdate()
        outermost = not connection.in_atomic_block
        with transaction.atomic():
            if outermost:  # inside a test's transaction it would stay read-only after this
                with connection.cursor() as cursor:
                    # One snapshot for every query, as the backup export takes (D-028).
                    cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            metric = day28_metric(session_days(), today=today)
            support = support_metrics(metric, today)
        self.stdout.write(report(metric, today, support))
