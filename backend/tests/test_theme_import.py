"""The "Novo tema" import: a pasted AI answer becomes a concept's subtopics (DECISIONS.md D-040).

Written by the agent; `tests/acceptance/` stays Diogo's.
"""

import textwrap
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from content.models import Content, Flashcard, ReviewLog
from content.parser import (
    contract_gaps,
    parse_markdown,
    split_documents,
    with_origin,
    without_reference_answers,
)
from content.services import create_manual_card, import_theme, rate_card
from django.db import connection
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

    text = with_origin(claimed, "gemini")

    assert parse_markdown(text).generated_by == "gemini"
    assert text.count("origem:") == 1


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
        "nivel: iniciante\n", "\n# gerado pela IA\nnivel: iniciante\ntags:\n  - docker\n- redes\n"
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
    preview = send(client, ANSWER, "/api/themes/preview/").json()

    response = send(client, ANSWER)

    # The screen offers the save for this alone, so the concept can join the track.
    assert all("entra também nesta trilha" in d["joins_track"] for d in preview["documents"])
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
def test_trilha_completa_alone_finishes_the_track_even_in_bold_or_with_a_period(client):
    answers = (
        "~~~~\nTRILHA COMPLETA\n~~~~",
        "**TRILHA COMPLETA**",
        "Trilha completa.",
        "Claro!\n\n~~~~markdown\nTRILHA COMPLETA\n~~~~",
        "TRILHA COMPLETA\n\nO tema já está coberto pelos conceitos da trilha.",
    )
    done = [send(client, a, "/api/themes/preview/").json() for a in answers]
    sentence = send(client, "Ainda não é a trilha completa.", "/api/themes/preview/").json()

    assert all(d["complete"] for d in done) and not sentence["complete"]
    assert "Nenhum documento" in sentence["errors"][0]


@pytest.mark.django_db
def test_an_ai_name_with_spaces_becomes_one_word(client):
    send(client, document("Camadas"), origem="Gemini Notebook")

    assert Content.objects.get().generated_by == "gemini-notebook"


# Found by the second review of PR #45.


def test_chat_headings_around_the_documents_are_ignored_not_saved():
    after = ANSWER.replace("Quer que eu", "## Próximos passos\nQuer que eu")
    between = (
        f"{FENCE}markdown\n{document('Imagem e container')}{FENCE}\n\n## Subtema 2: Camadas\n\n"
        f"{FENCE}markdown\n{document('Camadas')}{FENCE}\n"
    )
    labels = document("Imagem e container") + "\n### Subtema 2: Camadas\n\n" + document("Camadas")

    results = [split_documents(answer) for answer in (after, between, labels)]

    assert [documents for documents, _, _ in results] == [
        [document("Imagem e container"), document("Camadas")]
    ] * 3
    assert [ignored[-1] for _, ignored, _ in results] == [
        "## Próximos passos\nQuer que eu continue com o próximo conceito?",
        "## Subtema 2: Camadas",
        "### Subtema 2: Camadas",
    ]
    assert not any(cut for *_, cut in results)


@pytest.mark.django_db
def test_chat_naming_a_heading_or_a_subtema_does_not_block_but_a_lost_section_does(client):
    preamble = "## Conceito 3: Redes\n\n" + ANSWER
    closing = ANSWER + "\nNa próxima rodada sugiro o subtema: Volumes nomeados.\n"
    lost = "## Objetivo\nRodar um container.\n\n" + document("Camadas")

    reports = [send(client, a, "/api/themes/preview/").json() for a in (preamble, closing, lost)]

    assert [r["errors"] for r in reports[:2]] == [[], []]
    assert "Um trecho com títulos ficou fora" in reports[2]["errors"][0]


def test_a_code_fence_with_any_language_name_stays_inside_its_document():
    csharp = document("Imagem e container").replace(f"{FENCE}bash", f"{FENCE}c#")

    documents, _, cut = split_documents(f"~~~~markdown\n{csharp}\n{document('Camadas')}~~~~\n")

    assert documents == [csharp, document("Camadas")] and not cut


def test_a_star_in_a_name_is_kept_and_a_bold_key_loses_only_its_markers():
    star = document("*args e **kwargs")
    bold = document("Camadas").replace("subtema: Camadas", "**subtema:** Camadas")

    assert parse_markdown(star).frontmatter["subtema"] == "*args e **kwargs"
    assert parse_markdown(bold).frontmatter["subtema"] == "Camadas"


def test_a_bold_or_capitalized_answer_label_is_read_and_hidden_before_an_attempt():
    practice = (
        "### P1: O que é uma imagem?\n**Resposta de referência:** O molde.\n"
        "### P2: E um container?\nResposta de Referência: A execução.\n"
    )
    exact = "### P1: O que é uma imagem?\nResposta de referência: O molde.\n"

    parsed = parse_markdown(document("Camadas").replace(exact, practice))

    assert [q.reference_answer for q in parsed.questions] == ["O molde.", "A execução."]
    assert without_reference_answers(practice) == (
        "### P1: O que é uma imagem?\n### P2: E um container?"
    )


def test_questions_and_cards_the_parser_would_miss_show_as_gaps():
    base = document("Camadas")
    variants = {
        "Pergunta fora do formato": base.replace("### P1:", "**P1:**"),
        "Linha em Flashcards fora do formato": base.replace("- C2:", "  - C2:"),
        "Linha em Flashcards fora": base + "> - C3: Dentro de um destaque? :: Sim.\n",
        "Pergunta fora": base.replace("### P1:", "### Pergunta 1:"),
        "fora do separador": base.replace("Imagem ou container", "O que `std::vector` guarda,"),
    }
    fine = base.replace("### P1:", "P1 e P2 cobrem o básico.\n### P1:").replace(
        "- C2: De onde nasce um container? :: De uma imagem.",
        "- C2: Como imprimir em C++? :: std::cout << x;",
    )

    for gap, text in variants.items():
        assert any(gap in found for found in contract_gaps(parse_markdown(text))), gap
    assert not [g for g in contract_gaps(parse_markdown(fine)) if "Pergunta" in g or "::" in g]


# Found by the third review of PR #45.


def test_a_mention_of_the_answer_in_a_sentence_is_not_its_label():
    practice = (
        "### P1: O que roda primeiro?\n"
        "Compare depois com a resposta de referência: ela é curta.\n"
        "Resposta de referência:__init__ roda primeiro.\n"
    )
    exact = "### P1: O que é uma imagem?\nResposta de referência: O molde.\n"

    parsed = parse_markdown(document("Camadas").replace(exact, practice))

    assert parsed.questions[0].reference_answer == "__init__ roda primeiro."
    assert without_reference_answers(practice) == (
        "### P1: O que roda primeiro?\nCompare depois com a resposta de referência: ela é curta."
    )


def test_inline_backticks_or_a_chat_snippet_after_the_wrapper_never_hold_a_document():
    inline = document("Imagem e container").replace(
        "## Confusões comuns", "```docker ps``` lista os containers.\n## Confusões comuns"
    )
    snippet = (
        f"{FENCE}markdown\n{document('Imagem e container')}\n{document('Camadas')}{FENCE}\n\n"
        f"Se quiser, acrescento uma pergunta:\n\n{FENCE}markdown\n## Prática\n### P2: E o cache?\n"
        f"{FENCE}\n"
    )

    results = [
        split_documents(f"~~~~markdown\n{inline}\n{document('Camadas')}~~~~\n"),
        split_documents(snippet),
    ]

    assert [len(documents) for documents, _, _ in results] == [2, 2]
    assert results[1][0][1] == document("Camadas")
    assert "Se quiser" in results[1][1][-1]


@pytest.mark.django_db
def test_a_chat_line_naming_the_subtema_does_not_block_but_a_cut_frontmatter_does(client):
    named = ANSWER.replace("Quer que eu", "**Subtema:** Bind mounts\nQuer que eu")
    cut = ANSWER.replace(
        "Quer que eu continue com o próximo conceito?", "---\nconceito: X\nsubtema: Y"
    )

    reports = [send(client, a, "/api/themes/preview/").json() for a in (named, cut)]

    assert reports[0]["errors"] == []
    assert "Um trecho com títulos ficou fora" in reports[1]["errors"][0]


@pytest.mark.django_db
def test_errors_in_a_subtopic_that_keeps_its_text_do_not_block_the_new_ones(client):
    send(client, ANSWER)
    repeated = document("Camadas").replace("- C2:", "- C1:")

    response = send(client, repeated + "\n" + document("Volumes"))

    assert response.status_code == 201
    assert [d["action"] for d in response.json()["documents"]] == ["keep", "create"]
    assert Subtopic.objects.filter(name="Volumes").exists()


@pytest.mark.django_db(transaction=True)
def test_the_same_answer_saved_twice_at_once_is_created_once():
    start = threading.Barrier(4)

    def save(_):
        start.wait()
        try:
            return import_theme(
                area="Programação", track="Docker", origem="gemini", markdown=ANSWER, save=True
            )
        finally:
            connection.close()

    with ThreadPoolExecutor(4) as pool:
        reports = list(pool.map(save, range(4)))

    actions = sorted(d["action"] for report in reports for d in report["documents"])
    assert actions == ["create"] * 2 + ["same"] * 6
    assert Subtopic.objects.count() == 2


# Found by the fourth review of PR #45.


def test_a_card_cut_at_a_double_colon_in_code_is_listed():
    base = document("Camadas")
    cut = [
        base.replace("Imagem ou container executa?", "O que `lista[::2]` devolve?"),
        base.replace("Imagem ou container executa?", "O que o operador `::` faz em C++?"),
        base.replace(":: O container.", ":: O container. :: Sempre."),
    ]

    for text in cut:
        assert any("fora do separador" in g for g in contract_gaps(parse_markdown(text))), text


def test_an_answer_label_after_a_list_or_quote_marker_is_read_and_hidden():
    practice = (
        "### P1: O que é uma imagem?\n> **Resposta de Referência:** O molde.\n"
        "### P2: E um container?\n- **Resposta de referência:** A execução.\n"
        "### P3: E o cache?\n1. Resposta de referência: As camadas.\n"
        "### P4: E o volume?\n> - **Resposta de Referência:** Fica fora do container.\n"
    )
    exact = "### P1: O que é uma imagem?\nResposta de referência: O molde.\n"

    parsed = parse_markdown(document("Camadas").replace(exact, practice))

    assert [q.reference_answer for q in parsed.questions] == [
        "O molde.",
        "A execução.",
        "As camadas.",
        "Fica fora do container.",
    ]
    assert without_reference_answers(practice) == (
        "### P1: O que é uma imagem?\n### P2: E um container?\n### P3: E o cache?\n"
        "### P4: E o volume?"
    )


def test_a_question_merged_into_the_answer_before_it_is_listed_but_answer_headings_are_not():
    exact = "Resposta de referência: O molde.\n"
    merged = exact + "**Pergunta 2:** E um container?\nResposta de referência: A execução.\n"
    steps = "Resposta de referência: Em dois passos.\n#### Passo 1\nBaixar.\n#### Passo 2\nRodar.\n"
    unanswered = exact + "### P2 E um container?\n"

    gaps = [
        contract_gaps(parse_markdown(document("Camadas").replace(exact, t)))
        for t in (merged, steps, unanswered)
    ]

    assert any("Duas respostas de referência em P1" in g for g in gaps[0])
    assert not [g for g in gaps[1] if "Pergunta" in g or "Duas" in g]
    assert any("Pergunta fora do formato ### P1: ...: ### P2 E" in g for g in gaps[2])


def test_inline_triple_backticks_do_not_hide_the_sections_after_them():
    text = document("Camadas").replace(
        "## Confusões comuns", "```docker ps``` lista os containers.\n## Confusões comuns"
    )

    parsed = parse_markdown(text)

    assert (len(parsed.questions), len(parsed.cards), parsed.state) == (1, 2, "ready")


@pytest.mark.django_db
def test_a_new_subtopic_merged_into_one_that_keeps_its_text_blocks_the_save(client):
    send(client, ANSWER)
    volumes = document("Volumes").replace(
        "nivel: iniciante", "nivel: iniciante\nEste subtema cobre volumes nomeados."
    )
    edited = document("Camadas").replace("Texto.", "Texto novo.")

    report = send(client, f"{edited}\n{volumes}\n{document('Redes')}").json()

    assert report["documents"][0]["action"] == "keep"
    assert any("mais de uma vez" in e for e in report["documents"][0]["errors"])
    assert not Subtopic.objects.filter(name__in=["Volumes", "Redes"]).exists()


@pytest.mark.django_db
def test_a_trilha_completa_heading_is_a_plan_not_the_end_of_the_track(client):
    report = send(client, "## Trilha completa\n\n1. Imagens\n2. Volumes\n").json()

    assert not report["complete"]


# Found by the fifth review of PR #45.


def test_a_question_level_heading_or_an_unread_label_after_an_answer_is_listed():
    exact = "Resposta de referência: O molde.\n"
    challenge = exact + "### Desafio: Monte um Dockerfile multi-stage.\n"
    unread = exact + "### P2: E um container?\n**Resposta de referência**\nA execução.\n"

    gaps = [
        contract_gaps(parse_markdown(document("Camadas").replace(exact, t)))
        for t in (challenge, unread)
    ]

    assert any("Pergunta fora do formato ### P1: ...: ### Desafio" in g for g in gaps[0])
    assert "Pergunta sem resposta de referência: P2" in gaps[1]


def test_a_wrapper_read_late_still_closes_before_the_chat_after_it():
    yaml = "".join(
        document(name)
        .replace("---\narea", f"{FENCE}yaml\n---\narea", 1)
        .replace("nivel: iniciante\n---\n", f"nivel: iniciante\n---\n{FENCE}\n", 1)
        for name in ("Imagem e container", "Camadas")
    )
    chat = f"# Docker\nAqui estão os subtemas.\n**Subtema 1**\n{document('Imagem e container')}"

    for inside in (yaml, chat + document("Camadas")):
        documents, ignored, cut = split_documents(
            f"~~~~markdown\n{inside}~~~~\n\nQuer o próximo?\n"
        )

        assert len(documents) == 2 and "~~~~" not in documents[1], inside
        assert ignored[-1] == "Quer o próximo?" and not cut


# Found by the sixth review of PR #45.


def test_a_late_wrapper_left_open_is_a_cut_answer_and_a_chat_snippet_never_replaces_it():
    preface = f"# Docker\nRode antes:\n{FENCE}bash\ndocker --version\n{FENCE}\nDois subtemas.\n"
    docs = document("Imagem e container") + document("Camadas")

    closed = split_documents(f"~~~~markdown\n{preface}{docs}~~~~\nQuer o próximo?\n")
    cut = split_documents(f"~~~~markdown\n{preface}{docs[:-12]}")
    unwrapped = split_documents(f"Rode antes:\n{FENCE}bash\ndocker ps\n{FENCE}\n{docs}")

    assert closed[0] == [document("Imagem e container"), document("Camadas")]
    assert closed[1][-1] == "Quer o próximo?" and not closed[2]
    assert cut[2] and not unwrapped[2]


def test_text_between_a_question_and_its_answer_is_listed():
    exact = "### P1: O que é uma imagem?\nResposta de referência: O molde.\n"
    code = (
        "### P1: Reescreva este Dockerfile.\n```dockerfile\nCOPY . /app\n```\n"
        "**Resposta de referência:** Copie antes o requirements.\n"
    )

    gaps = contract_gaps(parse_markdown(document("Camadas").replace(exact, code)))

    assert any(g.startswith("Texto entre ### P1 e a resposta") for g in gaps)
    assert not [g for g in contract_gaps(parse_markdown(document("Camadas"))) if "Texto" in g]


@pytest.mark.django_db
def test_an_answer_cut_inside_the_next_frontmatter_blocks(client):
    cut = "---\narea: Programação\nconceito: Imagens e containers\nsubtema: Perfis e amb"

    report = send(client, document("Camadas") + "\n" + cut, "/api/themes/preview/").json()

    assert "frontmatter que não fechou" in report["documents"][0]["errors"][0]


@pytest.mark.django_db
def test_chat_decorations_do_not_hide_the_answer_label_a_heading_or_trilha_completa(client):
    exact = "Resposta de referência: O molde.\n"
    text = document("Camadas").replace(exact, "💡 **Resposta de referência:** O molde.\n")
    text = text.replace("## Pré-requisitos", "## Pré\u2011requisitos")

    parsed = parse_markdown(text)
    report = send(client, "✅ **TRILHA COMPLETA**\n", "/api/themes/preview/").json()

    assert parsed.questions[0].reference_answer == "O molde."
    assert not [g for g in contract_gaps(parsed) if "seç" in g]
    assert report["complete"]


# Found by the seventh review of PR #45.


@pytest.mark.django_db
def test_a_plan_titled_trilha_completa_is_not_the_end_of_the_track(client):
    plans = (
        "Veja o plano:\n\n**Trilha completa:**\n1. Imagens e containers\n2. Volumes\n",
        "- Trilha completa\n- Volumes\n",
        "Trilha completa?\nAinda faltam Volumes.\n",
    )

    reports = [send(client, p, "/api/themes/preview/").json() for p in plans]

    assert not [r for r in reports if r["complete"]]
    assert all("Nenhum documento" in r["errors"][0] for r in reports)


@pytest.mark.django_db
def test_an_answer_cut_before_the_next_subtema_line_blocks(client):
    for cut in ("---\narea: Programação", "---\narea: Programação\nconceito: Imagens e"):
        report = send(client, document("Camadas") + "\n" + cut, "/api/themes/preview/").json()

        assert any("frontmatter que não fechou" in e for e in report["documents"][0]["errors"]), cut

    footer = document("Camadas") + "---\n**Conceito:** pronto.\n"
    report = send(client, footer, "/api/themes/preview/").json()
    assert not [e for e in report["documents"][0]["errors"] if "frontmatter" in e]


def test_a_name_that_only_starts_and_ends_with_quoted_words_keeps_its_quotes():
    names = ('"Since" e "for"', '"Docker: imagens"', "'Camadas'")

    parsed = [parse_markdown(document(name)).frontmatter["subtema"] for name in names]

    assert parsed == ['"Since" e "for"', "Docker: imagens", "Camadas"]


def test_an_emoji_inside_the_bold_answer_label_is_read_and_hidden():
    practice = "### P1: O que é uma imagem?\n**💡 Resposta de referência:** O molde.\n"
    exact = "### P1: O que é uma imagem?\nResposta de referência: O molde.\n"

    parsed = parse_markdown(document("Camadas").replace(exact, practice))

    assert parsed.questions[0].reference_answer == "O molde."
    assert without_reference_answers(practice) == "### P1: O que é uma imagem?"


# Found by the eighth review of PR #45.


@pytest.mark.django_db
def test_an_answer_cut_inside_a_frontmatter_blocks_however_it_was_fenced(client):
    first = f"{FENCE}markdown\n{document('Imagem e container')}{FENCE}\n\n"
    fenced = first + f"{FENCE}markdown\n---\narea: Programação\nconceito: Imagens e containers"
    mid_key = document("Camadas") + "\n---\narea: Programação\nconc"

    fenced_report = send(client, fenced, "/api/themes/preview/").json()
    mid_key_report = send(client, mid_key, "/api/themes/preview/").json()

    assert any("fora dos documentos" in e for e in fenced_report["errors"])
    assert any("não fechou" in e for e in mid_key_report["documents"][0]["errors"])


def test_an_apostrophe_inside_a_single_quoted_name_is_not_a_quote():
    parsed = parse_markdown(document("'Don't panic'")).frontmatter["subtema"]

    assert parsed == "Don't panic"


def test_a_title_that_opens_in_bold_between_documents_is_chat_but_a_bold_card_is_not():
    titles = (
        "**Subtema 2:** Camadas",
        "**Subtema 2**: Camadas",
        "📘 **Subtema 2**",
        "2. **Camadas**",
    )
    card = "**C3:** E o cache? :: As camadas.\n"

    for title in titles:
        documents, ignored, _ = split_documents(
            f"~~~~markdown\n{document('Imagem e container')}\n---\n\n{title}\n\n"
            f"{document('Camadas')}~~~~\n"
        )

        assert documents == [document("Imagem e container"), document("Camadas")], title
        assert title in ignored
    assert split_documents(document("Camadas", extra=card))[0] == [document("Camadas", extra=card)]


def test_documents_nested_in_a_list_are_read_from_the_margin():
    answer = "".join(
        f"{n}.  **Subtema {n}**\n"
        + textwrap.indent(f"{FENCE}markdown\n{document(name)}{FENCE}\n", "    ")
        for n, name in ((1, "Imagem e container"), (2, "Camadas"))
    )

    documents, _, cut = split_documents(answer)

    assert documents == [document("Imagem e container"), document("Camadas")] and not cut
    assert len(parse_markdown(documents[1]).questions) == 1


@pytest.mark.django_db
def test_a_starred_plan_item_or_a_long_label_is_not_taken_for_something_else(client):
    plan = send(client, "* Trilha completa\n* Volumes\n", "/api/themes/preview/").json()
    long_label = document("Camadas").replace("- C2:", "- C12345678901:")

    response = send(client, long_label)

    assert not plan["complete"]
    assert response.status_code == 400
    assert "Rótulo com mais de 10 caracteres: C12345678901" in str(response.json())


# Found by the ninth review of PR #45.


@pytest.mark.django_db
def test_an_answer_cut_inside_a_frontmatter_with_bold_keys_blocks(client):
    cut = "\n---\n**area:** Programação\n**conceito:** Volumes no Docker"

    report = send(client, document("Camadas") + cut, "/api/themes/preview/").json()

    assert any("não fechou" in e for e in report["documents"][0]["errors"])


def test_an_indented_frontmatter_alone_leaves_the_body_as_written():
    code = "services:\n  web:\n    image: nginx\n"
    body = document("Camadas").replace("docker run hello-world\n", code)
    head, rest = body.split("---\n\n", 1)
    indented = textwrap.indent(head + "---\n", "  ") + "\n" + rest

    documents, _, _ = split_documents(f"~~~~markdown\n{indented}~~~~\n")

    assert code in documents[0]


def test_a_nested_document_keeps_its_sections_after_a_bare_code_fence():
    bare = document("Camadas").replace(f"{FENCE}bash\n", f"{FENCE}\n")
    answer = "1.  **Subtema 1**\n" + textwrap.indent(f"{FENCE}markdown\n{bare}{FENCE}\n", "    ")

    documents, _, cut = split_documents(answer)

    assert documents == [bare] and not cut


def test_a_quoted_chat_line_in_flashcards_is_listed_but_an_ia_callout_is_not():
    chat = document("Camadas", extra="> 💡 Quer que eu prepare o próximo conceito?\n")
    callout = document("Camadas", extra="> [!ia] Cartões gerados\n> confira as Fontes\n")

    gaps = [contract_gaps(parse_markdown(text)) for text in (chat, callout)]

    assert any(g.startswith("Linha em Flashcards fora do formato") for g in gaps[0])
    assert not [g for g in gaps[1] if "Flashcards" in g]


def test_accented_keys_yaml_escapes_and_hyphen_variants_read_as_written_in_the_template():
    text = document("'Don''t panic'", conceito="Copy‑on‑write").replace(
        "nivel: iniciante", "nível: intermediário"
    )

    parsed = parse_markdown(text)

    assert parsed.frontmatter["subtema"] == "Don't panic"
    assert parsed.frontmatter["conceito"] == "Copy-on-write"
    assert parsed.level == "intermediario"


# Found by the tenth review of PR #45.


def test_a_card_quoted_inside_an_ia_callout_is_listed():
    callout = "> [!ia] Este cartão não vem das fontes:\n> - C3: E o cache? :: As camadas.\n"

    gaps = contract_gaps(parse_markdown(document("Camadas", extra=callout)))

    assert any(g.endswith("> - C3: E o cache? :: As camadas.") for g in gaps)


def test_documents_nested_in_a_list_without_fences_are_read_from_their_indentation():
    answer = "".join(
        f"{n}.  **Subtema {n}**\n" + textwrap.indent(document(name), "   ")
        for n, name in ((1, "Imagem e container"), (2, "Camadas"))
    )

    documents, _, _ = split_documents(answer + "Bons estudos!\n")

    assert documents[0] == document("Imagem e container")
    assert [len(parse_markdown(d).questions) for d in documents] == [1, 1]


@pytest.mark.django_db
def test_a_bold_subtema_title_between_complete_documents_does_not_block(client):
    fenced = (
        document("Camadas")
        .replace("---\narea", f"{FENCE}yaml\n---\narea", 1)
        .replace("nivel: iniciante\n---\n", f"nivel: iniciante\n---\n{FENCE}\n", 1)
    )
    answer = document("Imagem e container") + "\n---\n**Subtema:** Camadas\n" + fenced

    report = send(client, answer, "/api/themes/preview/").json()

    assert [d["errors"] for d in report["documents"]] == [[], []]


@pytest.mark.django_db
def test_a_stored_name_with_a_non_breaking_hyphen_is_the_same_name(client):
    area = Area.objects.create(name="Programação")
    concept = Concept.objects.create(area=area, name="Copy‑on‑write")
    planned = Subtopic.objects.create(concept=concept, name="Camadas")

    send(client, document("Camadas", conceito="Copy‑on‑write"))

    assert Concept.objects.count() == 1
    assert Content.objects.filter(subtopic=planned).exists()


def test_frontmatter_keys_indented_with_a_tab_are_read():
    text = document("Camadas").replace(
        "\nnivel: iniciante", "\n\tnivel: avancado\n\torigem: claude"
    )

    parsed = parse_markdown(text)

    assert (parsed.level, parsed.generated_by) == ("avancado", "claude")
