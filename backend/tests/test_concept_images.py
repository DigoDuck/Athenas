"""Images in a subtopic's text: storage, credit, reading and backup (DECISIONS.md D-033).

Written by the agent; `tests/acceptance/` stays Diogo's.
"""

import base64

import pytest
from content.images import MAX_BYTES
from content.models import Block, Image
from content.parser import parse_markdown, split_segments
from content.services import import_content
from django.core.management import call_command
from django.utils import timezone
from organization.models import Area, Concept, Subtopic

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10"/></svg>'
CREDIT = {
    "source_url": "https://commons.wikimedia.org/wiki/File:Example.png",
    "author": "Fulano",
    "license": "CC BY-SA 4.0",
}
DOC = "## Ideia central\nUm agente repete um ciclo.\n\n## Explicação\nO ciclo tem três passos.\n"
WITH_IMAGE = DOC.replace(
    "Um agente repete um ciclo.\n",
    "Um agente repete um ciclo.\n\n![O ciclo do agente](/api/images/ciclo-do-agente/)\n",
)


def put_image(client, name, data, **fields):
    body = {"data": base64.b64encode(data).decode(), **fields}
    return client.put(f"/api/images/{name}/", body, content_type="application/json")


@pytest.fixture
def subtopic(db):
    area = Area.objects.create(name="Programação")
    concept = Concept.objects.create(area=area, name="Agentes de IA")
    return Subtopic.objects.create(concept=concept, name="O que é um agente")


def test_an_image_line_is_its_own_segment_and_code_keeps_it_as_code():
    line = '![Ciclo](/api/images/ciclo/ "O ciclo em três passos")'
    body = f"Antes.\n{line}\nDepois.\n```\n![x](/api/images/ciclo/)\n```"

    segments = split_segments(body)

    # The image keeps its line as written, so a screen that knows only Markdown still shows it.
    assert [(s.kind, s.text, s.image) for s in segments] == [
        ("text", "Antes.", None),
        ("image", line, "ciclo"),
        ("text", "Depois.", None),
        ("code", "![x](/api/images/ciclo/)", None),
    ]


def test_parsed_content_lists_each_image_once_in_order():
    again = "![De novo](/api/images/ciclo-do-agente/)"
    doc = f"{WITH_IMAGE}\n{again}\n![Outra](/api/images/turing/)\n![Fora](https://x.org/a.png)\n"

    assert parse_markdown(doc).images == ["ciclo-do-agente", "turing"]


@pytest.mark.django_db
def test_adding_an_image_to_a_read_block_keeps_its_read_mark(subtopic):
    import_content(subtopic, parse_markdown(DOC))
    read_at = timezone.now()
    Block.objects.filter(content__subtopic=subtopic).update(read_at=read_at)

    import_content(subtopic, parse_markdown(WITH_IMAGE))

    assert set(Block.objects.values_list("read_at", flat=True)) == {read_at}


@pytest.mark.django_db
def test_changing_the_text_beside_an_image_still_unmarks_the_block(subtopic):
    import_content(subtopic, parse_markdown(WITH_IMAGE))
    Block.objects.update(read_at=timezone.now())

    import_content(subtopic, parse_markdown(WITH_IMAGE.replace("um ciclo", "dois ciclos")))

    assert Block.objects.get(order=0).read_at is None
    assert Block.objects.get(order=1).read_at is not None


@pytest.mark.django_db
def test_a_credited_picture_is_stored_and_served_with_its_real_type(client):
    created = put_image(client, "ciclo-do-agente", PNG, **CREDIT)
    replaced = put_image(client, "ciclo-do-agente", PNG + b"\x01", **CREDIT)
    served = client.get("/api/images/ciclo-do-agente/")

    assert (created.status_code, replaced.status_code) == (201, 200)
    assert served["Content-Type"] == "image/png"
    assert served.content == PNG + b"\x01"
    assert served["X-Content-Type-Options"] == "nosniff"


@pytest.mark.django_db
def test_a_drawn_diagram_needs_only_who_drew_it_and_cannot_run_scripts(client):
    blank = {"source_url": "", "author": "", "license": ""}  # as scripts/theme.py sends it
    assert put_image(client, "loop", SVG, generated_by="Claude", **blank).status_code == 201

    served = client.get("/api/images/loop/")

    assert Image.objects.get().generated_by == "claude"
    assert served["Content-Type"] == "image/svg+xml"
    assert served["Content-Security-Policy"].startswith("default-src 'none'")


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("name", "data", "fields"),
    [
        ("sem-credito", PNG, {}),
        ("sem-licenca", PNG, {**CREDIT, "license": ""}),
        ("texto", b"not an image", CREDIT),
        ("grande", PNG + b"\x00" * MAX_BYTES, CREDIT),
        ("Maiuscula", PNG, CREDIT),
    ],
)
def test_an_image_without_source_type_size_or_valid_name_is_refused(client, name, data, fields):
    response = put_image(client, name, data, **fields)

    assert response.status_code == 400
    assert not Image.objects.exists()


@pytest.mark.django_db
def test_bad_base64_is_refused(client):
    response = client.put(
        "/api/images/x/", {"data": "não é base64"}, content_type="application/json"
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_reading_gives_each_image_its_url_and_credit(subtopic, client):
    put_image(client, "ciclo-do-agente", PNG, **CREDIT)
    import_content(subtopic, parse_markdown(WITH_IMAGE + "![Falta](/api/images/falta/)\n"))

    blocks = client.get(f"/api/subtopics/{subtopic.pk}/reading/").json()["blocks"]

    figure, missing = [s["image"] for b in blocks for s in b["segments"] if s["kind"] == "image"]
    assert figure == {
        "name": "ciclo-do-agente",
        "caption": "O ciclo do agente",
        "url": "/api/images/ciclo-do-agente/",
        "generated_by": "",
        **CREDIT,
    }
    assert (missing["caption"], missing["url"], missing["author"]) == ("Falta", None, "")


@pytest.mark.django_db
def test_the_preview_warns_about_an_image_not_uploaded(subtopic, client):
    response = client.post(
        f"/api/subtopics/{subtopic.pk}/content/preview/",
        {"markdown": WITH_IMAGE},
        content_type="application/json",
    )

    assert "Imagem não encontrada: ciclo-do-agente" in response.json()["warnings"]


@pytest.mark.django_db(transaction=True)
def test_a_backup_restores_the_image_bytes(tmp_path, settings, client):
    settings.BACKUP_DIR = str(tmp_path)
    put_image(client, "loop", SVG, generated_by="claude")
    call_command("backup")
    [export] = tmp_path.iterdir()

    call_command("flush", interactive=False)
    call_command("loaddata", str(export / "data.json"))

    assert bytes(Image.objects.get(name="loop").data) == SVG
