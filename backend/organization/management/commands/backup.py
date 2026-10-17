"""Daily export into the staging folder (spec 4.10, DECISIONS.md D-019 and D-028).

Each run exports when the last export is older than 24 h, then removes exports older than 30 days.
An export is a folder `athenas-<UTC stamp>` with `data.json` (every row of the app, the input of
`loaddata`) and `markdown/`, one file per subtopic in the content contract format.
"""

import re
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from content.models import Content
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils.text import slugify

STAMP = "%Y%m%d-%H%M%S"
EXPORT = re.compile(r"^athenas-(\d{8}-\d{6})$")
CATCH_UP = timedelta(hours=24)
KEEP = timedelta(days=30)


def exports(folder):
    """Finished exports in `folder`, oldest first, as (UTC time, path)."""
    found = []
    for path in folder.iterdir():
        match = EXPORT.match(path.name)
        if match and path.is_dir():
            try:
                found.append((datetime.strptime(match[1], STAMP).replace(tzinfo=UTC), path))
            except ValueError:  # a hand-made name with an impossible date
                continue
    return sorted(found)


def part(obj):
    # The pk keeps names unique and slugify keeps them valid on Windows and in Obsidian.
    return f"{obj.pk}-{slugify(obj.name)}"


def export(folder, now):
    final = folder / f"athenas-{now:{STAMP}}"
    # Written under another name first, so a crash never leaves a folder that looks finished.
    partial = final.with_name(final.name + ".partial")
    (partial / "markdown").mkdir(parents=True)
    data = partial / "data.json"
    # One snapshot for every table: a review saved mid-export must not leave a log without its
    # card, which would make loaddata fail at restore time.
    outermost = not connection.in_atomic_block
    with transaction.atomic():
        if outermost:  # only the first statement of a transaction can set its isolation
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        call_command("dumpdata", "organization", "content", "activity", indent=2, output=str(data))
        for content in Content.objects.select_related("subtopic__concept__area"):
            subtopic = content.subtopic
            concept = subtopic.concept
            path = partial / "markdown" / part(concept.area) / part(concept)
            path.mkdir(parents=True, exist_ok=True)
            (path / f"{part(subtopic)}.md").write_text(content.raw_markdown, encoding="utf-8")
    partial.rename(final)
    return final


class Command(BaseCommand):
    help = "Export JSON and Markdown to BACKUP_DIR when the last export is older than 24 h."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="export even if one is recent")

    def handle(self, *args, force=False, **options):
        if not settings.BACKUP_DIR:
            raise CommandError("BACKUP_DIR is not set.")
        folder = Path(settings.BACKUP_DIR)
        if not folder.is_dir():
            raise CommandError(f"{folder} is not a folder.")
        for leftover in folder.glob("athenas-*.partial"):
            shutil.rmtree(leftover)

        now = datetime.now(UTC)
        done = exports(folder)
        # A stamp ahead of the clock counts as stale, so a clock fix never blocks exports.
        if done and timedelta(0) <= now - done[-1][0] < CATCH_UP and not force:
            self.stdout.write(f"Skipped: {done[-1][1].name} is less than 24 h old.")
        else:
            done.append((now, export(folder, now)))
            self.stdout.write(f"Exported {done[-1][1].name}.")
        # The newest export is never removed, even after a month with the computer off.
        for when, path in done[:-1]:
            if now - when > KEEP:
                shutil.rmtree(path)
                self.stdout.write(f"Removed {path.name}.")
