"""Pure parser for the subtopic Markdown contract (spec 4.1 and 4.2). No Django, no database."""

import re
import unicodedata
from dataclasses import dataclass, field

CONTRACT_ORDER = (
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
)
KNOWN_HEADINGS = set(CONTRACT_ORDER)

QUESTION_RE = re.compile(r"^###\s+(P\d+):\s*(.+?)\s*$")
CARD_RE = re.compile(r"^-\s+(C\d+):\s*(.+?)\s*::\s*(.+?)\s*$")
CARD_LABEL_RE = re.compile(r"^-\s+(C\d+):")
SOURCE_RE = re.compile(r"Fonte:\s*(https?://\S+)")
# A code fence with any info string but a backtick (CommonMark): ```c#, ```c++, never
# "```ls``` lista", which is inline code at the start of a line.
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})([^`]*)$")
# One line on its own pointing at a stored image, `![legenda](/api/images/<nome>/)`, with the
# optional `"título"` the reading screen also takes as the caption (D-033).
IMAGE_RE = re.compile(r'^!\[([^\]]*)\]\(/api/images/([a-z0-9][a-z0-9-]*)/?(?:\s+"([^"]*)")?\)$')
# The label of spec 4.1 anywhere, as the parser always read it, or at the start of a line as chat
# AIs also write it: `**Resposta de referência:**`, `Resposta de Referência:`, `> - ...`. Never a
# lowercase mention in a sentence ("compare com a resposta de referência: ...").
REFERENCE_RE = re.compile(
    r"^[ \t]*(?:(?:[>*+-]|\d+[.)])[ \t]+)*(?P<m>[*_]+)?(?i:resposta de refer[êe]ncia)"
    r"(?:(?P=m):|:(?P=m)|:)"
    r"|Resposta de referência:",
    re.MULTILINE,
)
# A line in Prática that looks like a question but is not `### P<n>:`, so the parser would merge it
# into the previous answer: `**P2:**`, `### P2.`, `### P2 sem dois-pontos`, or any heading before
# an answer.
QUESTION_LIKE_RE = re.compile(r"^\W*P\d+\s*[:.)–-]|^#+\s*P\d+\b")
HEADING_RE = re.compile(r"^#{3,6}\s")
# Stored without accents, like `Subtopic.Level` ("intermediário" -> "intermediario").
LEVELS = {"iniciante", "intermediario", "avancado", "especialista"}
# Fits `Content.generated_by`.
GENERATED_BY_MAX = 30


@dataclass(frozen=True)
class Target:
    area: str
    conceito: str
    subtema: str


@dataclass(frozen=True)
class Block:
    kind: str
    heading: str
    body: str


@dataclass(frozen=True)
class Question:
    label: str
    prompt: str
    reference_answer: str | None


@dataclass(frozen=True)
class Card:
    label: str
    front: str
    back: str
    status: str = "pending"


@dataclass(frozen=True)
class Callout:
    text: str
    source: str | None

    @property
    def unsourced(self) -> bool:
        return self.source is None


@dataclass(frozen=True)
class Segment:
    kind: str  # "text", "code", "ia" or "image" (`text` is the line as written)
    text: str
    source: str | None = None
    image: str | None = None


@dataclass
class ParsedContent:
    raw: str = field(default="", compare=False)  # as pasted; "parses the same" ignores it
    level: str | None = None
    # Who wrote the text, from the frontmatter `origem` ("claude"); empty is Diogo (D-032).
    generated_by: str = ""
    frontmatter: dict[str, str] = field(default_factory=dict)
    blocks: list[Block] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)
    cards: list[Card] = field(default_factory=list)
    callouts: list[Callout] = field(default_factory=list)
    images: list[str] = field(default_factory=list)  # names, in order of first use
    state: str = "draft"
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def parse_markdown(text: str, target: Target | None = None) -> ParsedContent:
    """Parse one subtopic document. `errors` non-empty means the save is blocked."""
    raw = text
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    frontmatter, body = _split_frontmatter(text)
    parsed = ParsedContent(raw=raw, frontmatter=frontmatter)

    parsed.blocks = _split_blocks(body)
    for block in parsed.blocks:
        if block.kind == "Prática":
            parsed.questions = _parse_questions(block.body)
        elif block.kind == "Flashcards":
            parsed.cards, card_warnings = _parse_cards(block.body)
            parsed.warnings.extend(card_warnings)
    parsed.callouts = _parse_callouts(body)
    found = (s.image for b in parsed.blocks for s in split_segments(b.body) if s.kind == "image")
    parsed.images = list(dict.fromkeys(found))

    for label in _duplicates([q.label for q in parsed.questions]):
        parsed.errors.append(f"Rótulo duplicado: {label}")
    for label in _duplicates([c.label for c in parsed.cards]):
        parsed.errors.append(f"Rótulo duplicado: {label}")

    if target is not None:
        for key in ("area", "conceito", "subtema"):
            found = frontmatter.get(key)
            # Names match ignoring case (D-040), so "docker" is no news for "Docker".
            if found is not None and found.lower() != getattr(target, key).lower():
                parsed.warnings.append(
                    f"O frontmatter diz {key}: {found}, mas o conteúdo está sendo salvo em "
                    f"{getattr(target, key)}"
                )

    if nivel := frontmatter.get("nivel"):
        level = _without_accents(nivel).lower()
        if level in LEVELS:
            parsed.level = level
        else:
            parsed.warnings.append(f"Nível desconhecido no frontmatter: {nivel}; o nível não muda")

    if origem := frontmatter.get("origem", "").lower():
        # Cut, never dropped: an empty origin would pass generated text as Diogo's.
        parsed.generated_by = origem[:GENERATED_BY_MAX]
        if len(origem) > GENERATED_BY_MAX:
            parsed.warnings.append(f"Origem longa demais; fica {parsed.generated_by}")

    has_idea = any(b.kind == "Ideia central" and b.body for b in parsed.blocks)
    has_answered_question = any(q.reference_answer for q in parsed.questions)
    parsed.state = "ready" if has_idea and has_answered_question else "draft"
    return parsed


def _without_accents(value: str) -> str:
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    # Flat `key: value` lines only; the contract has no nested YAML, so no PyYAML dependency.
    lines = text.split("\n")
    if lines[0].strip() != "---":
        return {}, text
    for end, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            pairs = (item.partition(":") for item in lines[1:end])
            # Lowercase keys and plain values, as chat AIs also write `Subtema:` or `**subtema:**`.
            data = {k.strip(" *").lower(): _unquoted(_value(k, v)) for k, sep, v in pairs if sep}
            return data, "\n".join(lines[end + 1 :])
    return {}, text


def _value(key: str, value: str) -> str:
    # `**subtema:** Nome` leaves the bold marker on the value; `*args e **kwargs` is a name.
    if "*" in key:
        return value.strip().removeprefix("**").removesuffix("**").strip()
    return value.strip()


def _unquoted(value: str) -> str:
    # YAML quotes a value with a colon in it, and chat AIs often quote every value.
    if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1].strip()
    return value


def _fence_marker(line: str) -> str | None:
    """ "```" or "~~~" when the line opens or closes a fenced code block."""
    fence = FENCE_RE.match(line)
    return fence[1][:3] if fence else None


def _outside_fences(lines):
    """Yield (line, in_fence) so a `##` inside a fenced code block is never a heading."""
    fence = None
    for line in lines:
        marker = _fence_marker(line)
        if marker:
            if fence is None:
                fence = marker
                yield line, True
                continue
            if marker == fence:
                fence = None
                yield line, True
                continue
        yield line, fence is not None


def _split_blocks(body: str) -> list[Block]:
    blocks: list[Block] = []
    heading: str | None = None
    current: list[str] = []

    def close():
        body_text = "\n".join(current).strip()
        # Text before the first heading has no heading: keep it as an extra block ([C3]).
        if heading is not None or body_text:
            kind = heading if heading in KNOWN_HEADINGS else "extra"
            blocks.append(Block(kind, heading or "", body_text))

    for line, in_fence in _outside_fences(body.split("\n")):
        if not in_fence and line.startswith("## "):
            close()
            heading, current = line[3:].strip(), []
        else:
            current.append(line)
    close()
    return blocks


def _parse_questions(body: str) -> list[Question]:
    found: list[tuple[str, str, list[str]]] = []
    for line, in_fence in _outside_fences(body.split("\n")):
        match = None if in_fence else QUESTION_RE.match(line)
        if match:
            found.append((*match.groups(), []))
        elif found:
            found[-1][2].append(line)
    return [Question(label, prompt, _reference_answer(lines)) for label, prompt, lines in found]


def _reference_answer(lines: list[str]) -> str | None:
    # Everything after the marker, up to the next question; text before it is ignored.
    text = "\n".join(lines)
    marker = REFERENCE_RE.search(text)
    return (text[marker.end() :].strip() or None) if marker else None


def _parse_cards(body: str) -> tuple[list[Card], list[str]]:
    cards: list[Card] = []
    warnings: list[str] = []
    for line in body.split("\n"):
        if match := CARD_RE.match(line):
            cards.append(Card(*match.groups()))
        elif label := CARD_LABEL_RE.match(line):
            warnings.append(f"Cartão {label.group(1)} sem '::' entre frente e verso, ignorado")
    return cards, warnings


def _parse_callouts(body: str) -> list[Callout]:
    return [Callout(s.text, s.source) for s in split_segments(body) if s.kind == "ia"]


def split_segments(body: str) -> list[Segment]:
    """A body cut, in order, into plain text, fenced code and `> [!ia]` callouts."""
    segments: list[Segment] = []
    kind, lines, fence = "text", [], None

    def close():
        text = "\n".join(lines)
        if kind == "ia":
            source = SOURCE_RE.search(text)
            segments.append(Segment("ia", text, source.group(1) if source else None))
        elif kind == "code" or text.strip():
            segments.append(Segment(kind, text.strip("\n")))

    for line in body.split("\n"):
        marker, stripped = _fence_marker(line), line.strip()
        # Same fence rule as `_outside_fences`: a `##` or `> [!ia]` inside code is code.
        if fence:
            if marker == fence:
                close()
                kind, lines, fence = "text", [], None
            else:
                lines.append(line)
        elif marker:
            close()
            kind, lines, fence = "code", [], marker
        elif image := IMAGE_RE.match(stripped):
            close()
            segments.append(Segment("image", stripped, image=image[2]))
            kind, lines = "text", []
        elif stripped.startswith("> [!ia]"):
            close()
            kind, lines = "ia", [stripped[1:].strip()]
        elif kind == "ia" and stripped.startswith(">"):
            lines.append(stripped[1:].strip())
        else:
            if kind == "ia":
                close()
                kind, lines = "text", []
            lines.append(line)
    close()
    return segments


def reading_key(body: str) -> str:
    """The body as a read mark compares it: image and blank lines do not count (D-015, D-033)."""
    lines = (line.rstrip() for line in body.split("\n"))
    return "\n".join(line for line in lines if line and not IMAGE_RE.match(line.strip()))


def without_reference_answers(body: str) -> str:
    """The "Prática" body minus each reference answer, which shows only after an attempt (4.8.3).

    Cuts what `_reference_answer` reads: from the marker to the next question.
    """
    kept: list[str] = []
    in_question = hiding = False
    fence = None  # the fence open in `kept`, closed again if an answer starts inside it
    for line, in_fence in _outside_fences(body.split("\n")):
        if not in_fence and QUESTION_RE.match(line):
            in_question, hiding = True, False
        elif hiding:
            continue
        elif in_question and (marker := REFERENCE_RE.search(line)):
            hiding = True
            if before := line[: marker.start()].rstrip():
                kept.append(before)
            if fence:
                kept.append(fence)
                fence = None
            continue
        kept.append(line)
        marker = _fence_marker(line)
        if marker and fence in (None, marker):
            fence = None if fence else marker
    return "\n".join(kept).strip()


def _duplicates(labels: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: list[str] = []
    for label in labels:
        if label in seen and label not in dupes:
            dupes.append(label)
        seen.add(label)
    return dupes


# A pasted AI answer with several documents, for the "Novo tema" screen (DECISIONS.md D-040).

# A frontmatter key as chat AIs write it, sometimes indented or in bold (`**subtema:**`).
FRONTMATTER_KEY_RE = re.compile(r"^\s*\**([\w-]+)\**\s*:")
COMMENT_RE = re.compile(r"^\s*<!--.*-->\s*$")
# A heading or a line in bold alone, as chat AIs title each document ("**Subtema 2: Camadas**").
LABEL_RE = re.compile(r"^\s*(#{1,6}\s|\*\*[^*].*\*\*\s*$)")
FRONTMATTER_MAX = 40  # lines; the contract's frontmatter has five


def split_documents(text: str) -> tuple[list[str], list[str], bool]:
    """Cut an answer into subtopic documents, each starting at a frontmatter that names it.

    Chat AIs wrap the answer in a code fence, one around everything, one per document or one
    around each frontmatter, with chat text around them. One pass pairs the fences in order, as
    the reading does: a fence opened just before a frontmatter wraps documents, its closer ends
    them, and code fences inside a document stay in it. Returns the documents, the stretches of
    text outside every document (so the screen can show what was left out), and whether a
    wrapping fence never closed, the sign of an answer cut short.
    """
    text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    documents: list[list[str]] = []
    heads: list[int] = []  # frontmatter length of each document, which trimming never cuts
    ignored: list[list[str]] = [[]]
    wrapper = None  # the fence wrapping the documents: its character and length
    loose = None  # a fence opened in the chat, maybe a wrapper too far from the first frontmatter
    inner = None  # a code fence open inside a document
    outside = True
    i = 0
    while i < len(lines):
        line = lines[i]
        fence = FENCE_RE.match(line)
        if inner is None and (end := _frontmatter_end(lines, i)) is not None:
            documents.append(lines[i : end + 1])
            heads.append(end + 1 - i)
            outside = False
            i = end + 1
            if wrapper and (closer := _closes(lines, i, wrapper)) is not None:
                # A fence around the frontmatter alone (Gemini writes ```yaml): not a wrapper.
                i, wrapper = closer + 1, None
            continue
        if fence and inner is not None:
            inner = None if fence[1][:3] == inner else inner
        elif fence and wrapper is None and _opens_documents(lines, i + 1):
            wrapper, outside = (fence[1][0], len(fence[1])), True
            if loose and _is_closer(fence, loose):
                loose = None  # it also closed a chat snippet
            ignored.append([])
            i += 1
            continue
        elif fence and wrapper and _is_closer(fence, wrapper) and not _heading_ahead(lines, i + 1):
            wrapper, outside = None, True
            ignored.append([])
            i += 1
            continue
        elif fence and not outside:
            if (
                wrapper is None
                and loose
                and _is_closer(fence, loose)
                and not _heading_ahead(lines, i + 1)
            ):
                loose, outside = None, True  # its closer: what follows is chat again
                ignored.append([])
                i += 1
                continue
            inner = fence[1][:3]
        elif fence:
            loose = None if loose and _is_closer(fence, loose) else (fence[1][0], len(fence[1]))
        (ignored[-1] if outside else documents[-1]).append(line)
        i += 1

    texts = []
    for document, head in zip(documents, heads, strict=True):
        labels = []
        while len(document) > head:
            last = document[-1]
            if LABEL_RE.match(last) and not contract_heading(last) and not QUESTION_RE.match(last):
                labels.insert(0, last)
            elif not (last.strip() in ("", "---", "***", "___") or COMMENT_RE.match(last)):
                break
            document.pop()  # blank lines, rules and comments chat AIs put between documents
        ignored.append(labels)
        texts.append("\n".join(document) + "\n")
    stretches = ("\n".join(stretch).strip() for stretch in ignored)
    return texts, [stretch for stretch in stretches if stretch], wrapper is not None


def _frontmatter_end(lines: list[str], start: int) -> int | None:
    """The closing `---` of a frontmatter naming a `subtema` that opens at `start`, if one does.

    Blank, comment, indented and list lines may sit between the keys, as `_split_frontmatter`
    reads them; anything else means a `---` rule, not a frontmatter.
    """
    if start >= len(lines) or lines[start].strip() != "---":
        return None
    keys = set()
    for end in range(start + 1, min(start + FRONTMATTER_MAX, len(lines))):
        line = lines[end]
        stripped = line.strip()
        if stripped == "---":
            return end if "subtema" in keys else None
        if match := FRONTMATTER_KEY_RE.match(line):
            keys.add(match[1].lower())
        elif stripped and line[0] not in " \t" and not stripped.startswith(("# ", "- ")):
            return None
    return None


def _opens_documents(lines: list[str], start: int) -> bool:
    # A frontmatter within the next three filled lines, as when a chat writes "### Subtema 2"
    # between the fence and the frontmatter.
    for _ in range(3):
        start = _next_filled(lines, start)
        if _frontmatter_end(lines, start) is not None:
            return True
        if start >= len(lines) or FENCE_RE.match(lines[start]) or contract_heading(lines[start]):
            return False
        start += 1
    return False


def _heading_ahead(lines: list[str], start: int) -> bool:
    """Whether the document goes on after the code the fence at `start - 1` would open.

    Inside a ``` wrapper, a bare ``` may open an example as well as close the wrapper. Code it
    opens ends at the next bare fence, and then a contract heading must follow before the next
    frontmatter, outside any later code block: a chat heading ("## Próximos passos") or one in a
    chat snippet after the wrapper does not keep it open.
    """
    inner, fence = True, None  # in the code the fence would open; in a later code block
    for at in range(start, len(lines)):
        if fence is None and _frontmatter_end(lines, at) is not None:
            return False
        found = FENCE_RE.match(lines[at])
        if found and inner:
            if found[2].strip():
                return False  # a fence with a language opens code, it cannot end it
            inner = False
        elif found:
            fence = None if fence else found[1]
        elif not inner and fence is None and contract_heading(lines[at]):
            return True
    return False


def contract_heading(line: str) -> bool:
    return line.startswith("## ") and line[3:].strip() in KNOWN_HEADINGS


def _next_filled(lines: list[str], start: int) -> int:
    while start < len(lines) and not lines[start].strip():
        start += 1
    return start


def _is_closer(fence, wrapper) -> bool:
    return not fence[2].strip() and fence[1][0] == wrapper[0] and len(fence[1]) >= wrapper[1]


def _closes(lines, start, wrapper) -> int | None:
    """The index of a closer of `wrapper` at `start`, past blank lines, if there is one."""
    at = _next_filled(lines, start)
    fence = FENCE_RE.match(lines[at]) if at < len(lines) else None
    return at if fence and _is_closer(fence, wrapper) else None


def with_origin(text: str, origem: str) -> str:
    """The document with its frontmatter `origem` set to `origem`, replacing any it had."""
    lines = text.split("\n")
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    kept = [
        line
        for line in lines[1:end]
        if not ((key := FRONTMATTER_KEY_RE.match(line)) and key[1].lower() == "origem")
    ]
    return "\n".join(["---", *kept, f"origem: {origem}", *lines[end:]])


def contract_gaps(parsed: ParsedContent) -> list[str]:
    """What a complete generated document has and this one lacks; none of it blocks a save."""
    gaps = []
    kinds = [block.kind for block in parsed.blocks]
    if missing := [h for h in CONTRACT_ORDER if h not in kinds]:
        gaps.append(f"Faltam seções: {', '.join(missing)}")
    if "extra" in kinds:
        gaps.append("Há seção fora do contrato, ou texto antes do primeiro ##")
    if parsed.state != "ready":
        gaps.append("Rascunho: falta Ideia central ou uma pergunta com resposta de referência")
    if parsed.level is None:
        gaps.append("O frontmatter não diz o nivel")
    if not any(b.kind == "Fontes" and "http" in b.body for b in parsed.blocks):
        gaps.append("Fontes sem nenhum link")
    for block in (b for b in parsed.blocks if b.kind == "Prática"):
        odd, answer = [], False
        for line, in_fence in _outside_fences(block.body.split("\n")):
            if in_fence or QUESTION_RE.match(line):
                answer = answer and in_fence
                continue
            # An answer may have its own sub-headings (`#### Passo 1`), never a question's level.
            heading = HEADING_RE.match(line) and (not answer or line.startswith("### "))
            if QUESTION_LIKE_RE.match(line) or heading:
                odd.append(line)
            answer = answer or bool(REFERENCE_RE.search(line))
        if odd:
            gaps.append(f"Pergunta fora do formato ### P1: ...: {odd[0].strip()[:80]}")
    if unanswered := [q.label for q in parsed.questions if not q.reference_answer]:
        # Also the sign of a label written in a way the parser does not read.
        gaps.append(f"Pergunta sem resposta de referência: {unanswered[0]}")
    if merged := [
        q.label for q in parsed.questions if REFERENCE_RE.search(q.reference_answer or "")
    ]:
        gaps.append(
            f"Duas respostas de referência em {merged[0]}: uma pergunta fora do formato "
            "### P1: ... entrou nela"
        )
    for block in (b for b in parsed.blocks if b.kind == "Flashcards"):
        stray = []
        for raw in block.body.split("\n"):
            line = raw.strip()
            if not line or (CARD_LABEL_RE.match(raw) and not CARD_RE.match(raw)):
                continue  # empty, or a label without `::`, which already warns
            if CARD_RE.match(raw):
                # The parser cuts at the first `::`: one in code (`std::vector`, `[::2]`) or a
                # second spaced one means the front may end in the wrong place.
                before, _, after = raw.partition("::")
                if not (before[-1:].isspace() and after[:1].isspace()) or " :: " in after:
                    gaps.append(f"Cartão com '::' fora do separador ' :: ': {line[:80]}")
            # A `> [!ia]` callout may sit anywhere; anything else here would vanish from the cards.
            elif line[0] != ">" or CARD_LABEL_RE.match(line.lstrip("> ")):
                stray.append(line)
        if stray:
            gaps.append(f"Linha em Flashcards fora do formato - C1: ... :: ...: {stray[0][:80]}")
    if "Flashcards" in kinds and not parsed.cards:
        gaps.append("Nenhum cartão em Flashcards")
    return gaps
