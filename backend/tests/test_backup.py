"""Backup export, catch-up, retention and restore (spec 4.10, DECISIONS.md D-019 and D-028).

Written by the agent, outside tests/acceptance/. The Windows side (robocopy, the scheduled task)
is checked by hand; only its retention rule is tested here.
"""

import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from activity.models import SessionEvent
from activity.services import record_attempt, start_activity
from content.models import Content, Flashcard, ReviewLog
from content.parser import parse_markdown
from content.services import approve_card, import_content, rate_card
from django.core.management import call_command
from organization.models import Area, Concept, Subtopic

DOC = """## Ideia central
Esconder o estado interno.
"""


@pytest.fixture
def staging(tmp_path, settings):
    settings.BACKUP_DIR = str(tmp_path)
    return tmp_path


@pytest.fixture
def subtopic(db):
    area = Area.objects.create(name="Programação")
    concept = Concept.objects.create(area=area, name="Orientação a objetos")
    subtopic = Subtopic.objects.create(concept=concept, name="Encapsulamento: o quê?")
    import_content(subtopic, parse_markdown(DOC))
    return subtopic


def old_export(folder, age):
    path = folder / f"athenas-{datetime.now(UTC) - age:%Y%m%d-%H%M%S}"
    path.mkdir()
    return path


def names(folder):
    return sorted(p.name for p in folder.iterdir())


def test_export_writes_json_and_one_markdown_file_per_subtopic(staging, subtopic):
    call_command("backup")

    [export] = staging.iterdir()
    assert export.name.startswith("athenas-")
    data = json.loads((export / "data.json").read_text(encoding="utf-8"))
    assert {"organization.area", "content.content", "content.block"} <= {r["model"] for r in data}
    concept = subtopic.concept
    md = (
        export
        / "markdown"
        / f"{concept.area.pk}-programacao"
        / f"{concept.pk}-orientacao-a-objetos"
        / f"{subtopic.pk}-encapsulamento-o-que.md"
    )
    assert md.read_text(encoding="utf-8") == DOC


def test_export_is_skipped_when_the_last_one_is_under_24_hours_old(staging, db):
    recent = old_export(staging, timedelta(hours=23))

    call_command("backup")
    assert names(staging) == [recent.name]

    call_command("backup", force=True)
    assert len(names(staging)) == 2


def test_export_runs_when_the_last_one_is_over_24_hours_old(staging, db):
    old_export(staging, timedelta(hours=25))

    call_command("backup")

    assert len(names(staging)) == 2


def test_exports_older_than_30_days_are_removed_and_other_files_kept(staging, db):
    old = old_export(staging, timedelta(days=31))
    kept = old_export(staging, timedelta(days=29))
    (staging / "backup.log").write_text("log", encoding="utf-8")
    (staging / "athenas-20260101-000000.partial").mkdir()

    call_command("backup")

    found = names(staging)
    assert old.name not in found
    assert kept.name in found
    assert "backup.log" in found
    assert not any(name.endswith(".partial") for name in found)


@pytest.mark.django_db(transaction=True)
def test_restore_loads_the_json_back_into_an_empty_database(staging):
    area = Area.objects.create(name="Inglês")
    concept = Concept.objects.create(area=area, name="Phrasal verbs")
    subtopic = Subtopic.objects.create(concept=concept, name="Get")
    import_content(subtopic, parse_markdown(DOC + "\n## Flashcards\n- C1: get up :: levantar\n"))
    card = Flashcard.objects.get(subtopic=subtopic)
    approve_card(card)
    rate_card(card, "good")
    event = start_activity(SessionEvent.Kind.EXPLANATION, subtopic=subtopic)
    record_attempt(event, text="Phrasal verb.", self_assessment="right")
    call_command("backup")
    [export] = staging.iterdir()

    # The documented restore: flush, then loaddata.
    call_command("flush", interactive=False)
    assert not Content.objects.exists()
    call_command("loaddata", str(export / "data.json"))

    restored = Subtopic.objects.get(name="Get")
    assert restored.content.raw_markdown.startswith(DOC)
    assert restored.content.blocks.exists()
    assert restored.attempts.count() == 1
    assert ReviewLog.objects.filter(flashcard__pk=card.pk).count() == 1
    assert SessionEvent.objects.filter(completed_at__isnull=False).exists()
    # loaddata resets the sequences, so new rows do not collide with restored ids.
    assert Area.objects.create(name="Novo").pk > area.pk


def load_script():
    path = Path(__file__).resolve().parents[2] / "scripts" / "backup.py"
    spec = importlib.util.spec_from_file_location("backup_script", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_stamp_ahead_of_the_clock_does_not_block_the_export(staging, db):
    old_export(staging, -timedelta(hours=5))

    call_command("backup")

    assert len(names(staging)) == 2


def test_vault_retention_removes_only_old_exports_and_keeps_the_newest():
    expired = load_script().expired
    now = datetime(2026, 11, 20, 12, tzinfo=UTC)

    found = expired(
        [
            "athenas-20261001-120000",  # 50 days
            "athenas-20261025-120000",  # 26 days
            "Notas de estudo",
            "athenas-20261001-120000.partial",
            "athenas-20261399-000000",
        ],
        now,
    )
    assert found == ["athenas-20261001-120000"]
    assert expired(["athenas-20261001-120000"], now) == []
