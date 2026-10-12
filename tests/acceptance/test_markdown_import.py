"""Acceptance scenarios for the Markdown import parser (spec sections 4.1, 4.2 and 8).

Scenario numbers match section 8 of docs/spec.md. Scenario 39 covers only the warning here;
saving into the subtopic being edited belongs to the database slice.
"""

from content.parser import Target, parse_markdown

FRONT = (
    "---\n"
    "area: Programação\n"
    "conceito: Orientação a objetos\n"
    "subtema: Encapsulamento\n"
    "nivel: iniciante\n"
    "---\n"
)

KNOWN_HEADINGS = [
    "Objetivo",
    "Pré-requisitos",
    "Ideia central",
    "Explicação",
    "Exemplo",
    "Confusões comuns",
    "Prática",
    "Resumo para o caderno",
    "Fontes",
    "Flashcards",
]

IDEIA = "## Ideia central\nEsconder o estado interno do objeto."
PRATICA_COM_RESPOSTA = (
    "## Prática\n"
    "### P1: Qual problema o encapsulamento resolve?\n"
    "Resposta de referência: Evita acesso direto ao estado interno."
)
PRATICA_SEM_RESPOSTA = "## Prática\n### P1: Qual problema o encapsulamento resolve?"


def md(*sections):
    return FRONT + "\n" + "\n\n".join(sections) + "\n"


def test_16_content_without_ideia_central_is_draft():
    parsed = parse_markdown(md(PRATICA_COM_RESPOSTA))

    assert parsed.state == "draft"


def test_17_content_whose_only_question_has_no_reference_answer_is_draft():
    parsed = parse_markdown(md(IDEIA, PRATICA_SEM_RESPOSTA))

    assert parsed.state == "draft"


def test_18_content_with_ideia_central_and_answered_question_is_ready():
    parsed = parse_markdown(md(IDEIA, PRATICA_COM_RESPOSTA))

    assert parsed.state == "ready"


def test_26_each_known_heading_becomes_its_own_block_in_order():
    sections = [f"## {heading}\nTexto de {heading}." for heading in KNOWN_HEADINGS]

    parsed = parse_markdown(md(*sections))

    assert [b.heading for b in parsed.blocks] == KNOWN_HEADINGS
    assert [b.kind for b in parsed.blocks] == KNOWN_HEADINGS


def test_27_unknown_heading_becomes_extra_block_in_its_original_position():
    parsed = parse_markdown(
        md("## Exemplo\nUm exemplo.", "## Curiosidades\nAlgo a mais.", PRATICA_COM_RESPOSTA)
    )

    assert [b.heading for b in parsed.blocks] == ["Exemplo", "Curiosidades", "Prática"]
    assert [b.kind for b in parsed.blocks] == ["Exemplo", "extra", "Prática"]
    assert parsed.blocks[1].body == "Algo a mais."


def test_28_p1_with_reference_answer_becomes_a_question():
    parsed = parse_markdown(md(PRATICA_COM_RESPOSTA))

    assert len(parsed.questions) == 1
    question = parsed.questions[0]
    assert question.label == "P1"
    assert question.prompt == "Qual problema o encapsulamento resolve?"
    assert question.reference_answer == "Evita acesso direto ao estado interno."


def test_29_c1_front_and_back_becomes_a_pending_card():
    flashcards = (
        "## Flashcards\n"
        "- C1: O que o encapsulamento esconde? :: O estado interno do objeto; "
        "o acesso passa por métodos."
    )

    parsed = parse_markdown(md(flashcards))

    assert len(parsed.cards) == 1
    card = parsed.cards[0]
    assert card.label == "C1"
    assert card.front == "O que o encapsulamento esconde?"
    assert card.back == "O estado interno do objeto; o acesso passa por métodos."
    assert card.status == "pending"


def test_36_two_c1_labels_in_one_document_block_the_save():
    flashcards = "## Flashcards\n- C1: Primeira frente :: Primeiro verso\n- C1: Outra :: Outro"

    parsed = parse_markdown(md(flashcards))

    assert len(parsed.errors) == 1
    assert "C1" in parsed.errors[0]


def test_37_ia_callout_without_a_fonte_url_is_marked_as_unsourced():
    callout = "> [!ia] Complemento sugerido pela IA\n> Texto do complemento, sem fonte."

    parsed = parse_markdown(md(IDEIA, callout))

    assert len(parsed.callouts) == 1
    assert parsed.callouts[0].unsourced is True


def test_38_ia_callout_with_a_fonte_url_is_not_marked():
    callout = (
        "> [!ia] Complemento sugerido pela IA\n"
        "> Texto do complemento.\n"
        "> Fonte: https://example.com/encapsulamento"
    )

    parsed = parse_markdown(md(IDEIA, callout))

    assert len(parsed.callouts) == 1
    assert parsed.callouts[0].unsourced is False
    assert parsed.callouts[0].source == "https://example.com/encapsulamento"


def test_39_frontmatter_naming_another_subtopic_shows_a_warning():
    target = Target(area="Programação", conceito="Orientação a objetos", subtema="Herança")

    parsed = parse_markdown(md(IDEIA, PRATICA_COM_RESPOSTA), target=target)

    assert len(parsed.warnings) == 1
    assert "subtema" in parsed.warnings[0]


# Extra scenarios, not in spec section 8 (edge cases of the import rules).


def test_a_heading_inside_a_fenced_code_block_does_not_become_a_block():
    exemplo = "## Exemplo\n```python\n## isto é um comentário\nx = 1\n```"

    parsed = parse_markdown(md(exemplo, IDEIA))

    assert [b.heading for b in parsed.blocks] == ["Exemplo", "Ideia central"]
    assert "## isto é um comentário" in parsed.blocks[0].body


def test_b_crlf_text_parses_the_same_as_lf_text():
    lf = md(IDEIA, PRATICA_COM_RESPOSTA)

    crlf = parse_markdown(lf.replace("\n", "\r\n"))

    assert crlf == parse_markdown(lf)


def test_c_multi_line_reference_answer_is_kept_whole():
    pratica = (
        "## Prática\n"
        "### P1: Qual problema o encapsulamento resolve?\n"
        "Resposta de referência: Evita acesso direto ao estado interno.\n"
        "Também permite mudar a implementação sem quebrar quem usa a classe.\n"
        "### P2: Outra pergunta?\n"
        "Resposta de referência: Outra resposta."
    )

    parsed = parse_markdown(md(pratica))

    assert parsed.questions[0].reference_answer == (
        "Evita acesso direto ao estado interno.\n"
        "Também permite mudar a implementação sem quebrar quem usa a classe."
    )
    assert parsed.questions[1].reference_answer == "Outra resposta."


def test_d_text_before_the_first_heading_is_not_discarded():
    parsed = parse_markdown(FRONT + "\nTexto solto antes de tudo.\n\n" + IDEIA + "\n")

    assert [b.kind for b in parsed.blocks] == ["extra", "Ideia central"]
    assert parsed.blocks[0].body == "Texto solto antes de tudo."


def test_e_content_without_frontmatter_parses_with_empty_frontmatter():
    parsed = parse_markdown(IDEIA + "\n\n" + PRATICA_COM_RESPOSTA + "\n")

    assert parsed.frontmatter == {}
    assert parsed.state == "ready"


def test_f_card_line_without_double_colon_warns_and_is_not_a_card():
    flashcards = "## Flashcards\n- C1: Frente sem verso"

    parsed = parse_markdown(md(flashcards))

    assert parsed.cards == []
    assert len(parsed.warnings) == 1
    assert "C1" in parsed.warnings[0]
