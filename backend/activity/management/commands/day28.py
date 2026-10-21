"""Day 28 metric (spec 4.11.2, DECISIONS.md D-010, D-029 and D-038).

Prints the blocks and the reading that applies as Markdown for the verdict entry. It runs against
use mode's real data, so it only reads, inside a read-only transaction.
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from activity.services import day28_metric, session_days

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


def report(metric, today):
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
    lines += [
        f"Reading: {READINGS[metric['reading']]}",
        "",
        "Not in the session events, to be written by hand: the features that shipped that month "
        "and the sessions lost to being away from the computer.",
    ]
    return "\n".join(lines)


class Command(BaseCommand):
    help = "Print the day 28 blocks and the D-010 reading. Reads only."

    def add_arguments(self, parser):
        parser.add_argument(
            "--today", type=date.fromisoformat, help="Bahia date to read on (default: today)"
        )

    def handle(self, *args, today=None, **options):
        outermost = not connection.in_atomic_block
        with transaction.atomic():
            if outermost:  # inside a test's transaction it would stay read-only after this
                with connection.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
            days = session_days()
        today = today or timezone.localdate()
        self.stdout.write(report(day28_metric(days, today=today), today))
