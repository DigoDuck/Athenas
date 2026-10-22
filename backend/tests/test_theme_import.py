"""The "Novo tema" import: a pasted AI answer becomes a concept's subtopics (DECISIONS.md D-040).

Written by the agent; `tests/acceptance/` stays Diogo's.
"""

import pytest
from content.models import Content, Flashcard, ReviewLog
from content.parser import contract_gaps, parse_markdown, split_documents, with_origin
from content.services import create_manual_card, import_theme, rate_card
from organization.models import Area, Concept, Step, Subtopic, Track

FENCE = "```"


def document(subtema, conceito="Imagens e containers", extra=""):
    return (
        "---\n"
        "area: Programação\n"
        f"conceito: {conceito}\n"
        f"subtema: {subtema}\n"
        "nivel: iniciante\n"
        "---\n\n"
        "## Objetivo\nRodar um container.\n"
        "## Pré-requisitos\nTerminal.\n"
        "## Ideia central\nUma imagem é o molde; o container, a execução.\n"
        "## Explicação\nTexto.\n"
        f"## Exemplo\n{FENCE}bash\ndocker run hello-world\n{FENCE}\n"
        "## Confusões comuns\nImagem não é container.\n"
        "## Prática\n### P1: O que é uma imagem?\nResposta de referência: O molde.\n"
        "## Resumo para o caderno\nImagem: molde.\n"
        "## Fontes\n- https://docs.docker.com/get-started/\n"
        "## Flashcards\n- C1: Imagem ou container executa? :: O container.\n"
        "- C2: De onde nasce um container? :: De uma imagem.\n"
        f"{extra}"
    )


ANSWER = f"""Claro! Aqui está o conceito.

~~~~markdown
{document("Imagem e container")}
---
{document("Camadas")}~~~~

Quer que eu continue com o próximo conceito?
"""


def test_a_wrapped_answer_splits_into_its_documents_and_reports_the_chat_around_them():
    documents, ignored, _ = split_documents(ANSWER)

    assert documents == [document("Imagem e container"), document("Camadas")]
    assert ignored == [
        "Claro! Aqui está o conceito.",
        "Quer que eu continue com o próximo conceito?",
    ]


def test_one_fence_per_document_keeps_the_code_inside_and_drops_the_text_between():
    answer = (
        f"{FENCE}markdown\n{document('Imagem e container')}{FENCE}\n\nAgora o segundo:\n\n"
        f"{FENCE}md\n{document('Camadas')}{FENCE}\n"
    )

    documents, ignored, _ = split_documents(answer.replace("\n", "\r\n"))

    assert documents == [document("Imagem e container"), document("Camadas")]
    assert ignored == ["Agora o segundo:"]


def test_a_rule_in_a_body_or_text_without_frontmatter_is_never_a_new_document():
    rule = document("Imagem e container", extra="\n---\nNota depois de uma linha.\n")

    assert split_documents(rule) == ([rule], [], False)
    rendered = "## Ideia central\nTexto copiado da tela, sem frontmatter."
    assert split_documents(rendered) == ([], [rendered], False)


def test_the_origin_chosen_on_the_screen_replaces_the_one_the_answer_claims():
    claimed = document("Camadas").replace("nivel: iniciante", "nivel: iniciante\norigem: claude")

    parsed = parse_markdown(with_origin(claimed, "gemini"))

    assert parsed.generated_by == "gemini"
    assert list(parsed.frontmatter).count("origem") == 1


def send(client, markdown, path="/api/themes/", **fields):
    body = {"area": "Programação", "track": "Docker", "origem": "Gemini", "markdown": markdown}
    return client.post(path, body | fields, content_type="application/json")


@pytest.mark.django_db
def test_preview_reports_each_document_and_writes_nothing(client):
    response = send(client, ANSWER, "/api/themes/preview/")

    report = response.json()
    assert response.status_code == 200
    assert report["area_new"] and report["track_new"]
    assert [(d["subtema"], d["action"], d["cards"]) for d in report["documents"]] == [
        ("Imagem e container", "create", 2),
        ("Camadas", "create", 2),
    ]
    assert report["documents"][0]["warnings"] == []
    assert not (Area.objects.exists() or Track.objects.exists() or Content.objects.exists())


@pytest.mark.django_db
def test_save_creates_the_track_concept_and_subtopics_in_order_with_cards_pending(client):
    response = send(client, ANSWER)

    assert response.status_code == 201
    assert response.json()["pending"] == 4
    track = Track.objects.get(name="Docker")
    assert [s.concept.name for s in track.steps.all()] == ["Imagens e containers"]
    concept = Concept.objects.get(area__name="Programação", name="Imagens e containers")
    assert [s.name for s in concept.subtopics.all()] == ["Imagem e container", "Camadas"]
    assert set(Content.objects.values_list("generated_by", "state")) == {("gemini", "ready")}
    assert set(Flashcard.objects.values_list("state", flat=True)) == {Flashcard.State.PENDING}
    assert Subtopic.objects.filter(level="iniciante").count() == 2


@pytest.mark.django_db
def test_the_next_round_appends_its_concept_to_the_same_track(client):
    send(client, ANSWER)
    second = document("Volumes", conceito="Dados e volumes")

    send(client, second)

    steps = Track.objects.get(name="Docker").steps.all()
    assert [s.concept.name for s in steps] == ["Imagens e containers", "Dados e volumes"]


@pytest.mark.django_db
def test_pasting_again_changes_nothing_and_never_touches_text_already_there(client):
    send(client, ANSWER)
    subtopic = Subtopic.objects.get(name="Camadas")
    edited = Content.objects.get(subtopic=subtopic).raw_markdown + "Nota do Diogo.\n"
    Content.objects.filter(subtopic=subtopic).update(raw_markdown=edited)
    Flashcard.objects.filter(subtopic=subtopic, label="C1").update(state=Flashcard.State.ACTIVE)

    changed = document("Camadas").replace("De uma imagem.", "Do Dockerfile.")
    response = send(client, document("Imagem e container") + changed)

    assert response.status_code == 201
    assert [d["action"] for d in response.json()["documents"]] == ["same", "keep"]
    assert response.json()["pending"] == 0
    assert Content.objects.get(subtopic=subtopic).raw_markdown == edited
    assert Flashcard.objects.get(subtopic=subtopic, label="C1").state == Flashcard.State.ACTIVE
    assert Flashcard.objects.get(subtopic=subtopic, label="C2").back == "De uma imagem."
    assert Step.objects.count() == 1


@pytest.mark.django_db
def test_an_existing_concept_is_reused_and_an_empty_subtopic_is_filled(client):
    area = Area.objects.create(name="Programação")
    concept = Concept.objects.create(area=area, name="Imagens e containers")
    planned = Subtopic.objects.create(concept=concept, name="Camadas")

    send(client, ANSWER)

    assert Concept.objects.count() == 1
    assert Content.objects.get(subtopic=planned).generated_by == "gemini"
    assert [s.name for s in concept.subtopics.all()] == ["Camadas", "Imagem e container"]


@pytest.mark.django_db
def test_one_blocked_document_blocks_the_whole_answer(client):
    broken = document("Camadas", extra="- C1: Repetido :: Repetido.\n")

    response = send(client, document("Imagem e container") + broken)

    assert response.status_code == 400
    assert response.json()["documents"][1]["errors"] == ["Rótulo duplicado: C1"]
    assert not (Area.objects.exists() or Track.objects.exists() or Subtopic.objects.exists())


@pytest.mark.django_db
def test_missing_names_and_repeated_subtopics_block_the_save(client):
    nameless = document("Camadas").replace("subtema: Camadas\n", "")
    nameless = nameless.replace("conceito:", "subtema: Camadas\nconceito:", 1)
    unnamed = document("X").replace("conceito: Imagens e containers\n", "")

    report = send(client, document("Camadas") + nameless + unnamed).json()

    assert report["documents"][1]["errors"] == [
        "Subtema repetido na resposta: Imagens e containers / Camadas"
    ]
    assert report["documents"][2]["errors"] == ["O frontmatter precisa de conceito e subtema"]
    assert not Subtopic.objects.exists()


@pytest.mark.django_db
def test_an_answer_copied_as_rendered_text_or_an_unsafe_origin_is_refused(client):
    rendered = send(client, "Ideia central\nUma imagem é o molde.")
    injected = send(client, ANSWER, origem="gemini\nconceito: Outro")

    assert rendered.status_code == 400
    assert "Nenhum documento" in rendered.json()["errors"][0]
    assert injected.status_code == 400
    assert "origem" in injected.json()
    assert not Area.objects.exists()


@pytest.mark.django_db
def test_gaps_in_the_contract_warn_without_blocking(client):
    thin = (
        "---\nconceito: Imagens e containers\nsubtema: Camadas\n---\n"
        "## Ideia central\nCamadas.\n> [!ia] Sem fonte.\n"
    )

    response = send(client, thin)

    document_report = response.json()["documents"][0]
    assert response.status_code == 201
    assert document_report["state"] == "draft"
    assert document_report["unsourced"] == 1
    assert any("Faltam seções" in w for w in document_report["warnings"])
    assert any("Fontes" in w for w in document_report["warnings"])
    assert Content.objects.get().state == "draft"


# Found by the adversarial review of PR #45: each test reproduces one finding.


def test_a_frontmatter_with_blank_comment_or_list_lines_still_starts_its_document():
    loose = document("Camadas").replace(
        "nivel: iniciante\n", "\n# gerado pela IA\nnivel: iniciante\ntags:\n  - docker\n"
    )

    documents, *_ = split_documents(document("Imagem e container") + loose)

    assert [parse_markdown(d).frontmatter["subtema"] for d in documents] == [
        "Imagem e container",
        "Camadas",
    ]


def test_quoted_names_and_capitalized_keys_read_as_plain_values():
    quoted = document("Camadas").replace("subtema: Camadas", 'Subtema: "Camadas: cache"')

    assert parse_markdown(quoted).frontmatter["subtema"] == "Camadas: cache"


def test_a_fence_around_the_frontmatter_alone_keeps_the_whole_document():
    gemini = document("Camadas").replace("---\n", f"**Subtema 1**\n{FENCE}yaml\n---\n", 1)
    gemini = gemini.replace("nivel: iniciante\n---\n", f"nivel: iniciante\n---\n{FENCE}\n", 1)

    documents, ignored, _ = split_documents(gemini)

    assert ignored == ["**Subtema 1**"]
    assert len(parse_markdown(documents[0]).cards) == 2
    assert "## Flashcards" in documents[0]


@pytest.mark.django_db
def test_an_answer_cut_after_a_frontmatter_blocks_instead_of_failing():
    header = document("Camadas").split("## Objetivo")[0]
    cut = ANSWER.split("Quer que")[0].replace(document("Camadas"), header)

    report = import_theme(area="Programação", track="Docker", origem="gemini", markdown=cut)

    assert report["documents"][1]["errors"] == [
        "Documento sem texto depois do frontmatter: a resposta foi cortada?"
    ]


def test_chat_text_left_in_flashcards_shows_as_a_gap():
    chatty = document("Camadas") + "\nQuer que eu continue com o próximo conceito?\n"
    bullets = document("Imagem e container").replace("- C1:", "*   C1:")

    gaps = [contract_gaps(parse_markdown(d)) for d in (chatty, bullets)]

    assert any("Quer que eu continue" in gap for gap in gaps[0])
    assert any("*   C1:" in gap for gap in gaps[1])


@pytest.mark.django_db
def test_a_fill_import_never_suspends_diogos_manual_cards(client):
    area = Area.objects.create(name="Programação")
    concept = Concept.objects.create(area=area, name="Imagens e containers")
    planned = Subtopic.objects.create(concept=concept, name="Camadas")
    mine = [create_manual_card(front=f"Minha {n}", back="Verso", subtopic=planned) for n in (1, 2)]
    rate_card(mine[0], ReviewLog.Rating.GOOD)

    send(client, document("Camadas"))

    states = set(Flashcard.objects.filter(origin="manual").values_list("state", flat=True))
    assert states == {Flashcard.State.ACTIVE}
    assert ReviewLog.objects.count() == 1


@pytest.mark.django_db
def test_a_kept_or_identical_document_still_puts_its_concept_in_the_track(client):
    send(client, ANSWER, track="Outra")

    response = send(client, ANSWER)

    assert [d["action"] for d in response.json()["documents"]] == ["same", "same"]
    assert [s.concept.name for s in Track.objects.get(name="Docker").steps.all()] == [
        "Imagens e containers"
    ]


@pytest.mark.django_db
def test_names_match_existing_rows_ignoring_case(client):
    send(client, ANSWER)
    other_case = document("camadas", conceito="imagens e containers")

    response = send(client, other_case, area="programação", track="docker")

    report = response.json()["documents"][0]
    assert report["action"] == "keep"
    assert not [w for w in report["warnings"] if w.startswith("O frontmatter diz")]
    assert (Area.objects.count(), Track.objects.count(), Concept.objects.count()) == (1, 1, 1)


@pytest.mark.django_db
def test_template_names_merged_documents_and_lost_headings_block_the_save(client):
    template = document("<nome do subtema>", conceito="<nome do conceito>")
    merged = document("Imagem e container") + document("Camadas").replace("---\n", "--- \n", 1)
    merged = merged.replace("subtema: Camadas", "Subtema Camadas")

    reports = [send(client, text).json() for text in (template, merged)]

    assert "modelo do pedido" in reports[0]["documents"][0]["errors"][0]
    assert any("mais de uma vez" in e for e in reports[1]["documents"][0]["errors"])
    assert not Subtopic.objects.exists()


@pytest.mark.django_db
def test_a_concept_from_another_track_is_named_before_it_receives_subtopics(client):
    send(client, ANSWER, track="Python")

    report = send(client, document("Volumes"), "/api/themes/preview/").json()

    assert any("trilha Python" in w for w in report["documents"][0]["warnings"])


@pytest.mark.django_db
def test_only_a_bare_trilha_completa_counts_as_a_finished_track(client):
    done = send(client, "~~~~\nTRILHA COMPLETA\n~~~~", "/api/themes/preview/").json()
    sentence = send(client, "Ainda não é a trilha completa.", "/api/themes/preview/").json()

    assert done["complete"] and not sentence["complete"]
    assert "Nenhum documento" in sentence["errors"][0]


@pytest.mark.django_db
def test_an_ai_name_with_spaces_becomes_one_word(client):
    send(client, document("Camadas"), origem="Gemini Notebook")

    assert Content.objects.get().generated_by == "gemini-notebook"
