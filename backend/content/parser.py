"""Pure parser for the subtopic Markdown contract (spec 4.1 and 4.2). No Django, no database."""

import os
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

# The text trimmed with no lazy group, so a run of spaces reads at once, as in CARD_RE.
QUESTION_RE = re.compile(r"^###\s+(P\d+):\s*(\S(?:.*\S)?|\s)\s*$")
# The front ends at the first `::`, never blank; no lazy group, so a run of spaces reads at once.
CARD_RE = re.compile(
    r"^-\s+(C\d+):\s*+(\S(?:(?!::)\S|\s+(?=\S)(?!::))*)\s*::\s*(\S(?:.*\S)?|\s)\s*$"
)
LABEL_MAX = 10  # PracticeQuestion.label and Flashcard.label
CARD_LABEL_RE = re.compile(r"^-\s+(C\d+):")
SOURCE_RE = re.compile(r"Fonte:\s*(https?://\S+)")
# A code fence with any info string but a backtick (CommonMark): ```c#, ```c++, never
# "```ls``` lista", which is inline code at the start of a line. The run never backtracks.
FENCE_RE = re.compile(r"^\s*(`{3,}+|~{3,}+)([^`]*)$")
# One line on its own pointing at a stored image, `![legenda](/api/images/<nome>/)`, with the
# optional `"título"` the reading screen also takes as the caption (D-033).
IMAGE_RE = re.compile(r'^!\[([^\]]*)\]\(/api/images/([a-z0-9][a-z0-9-]*)/?(?:\s+"([^"]*)")?\)$')
# The label of spec 4.1 anywhere, as the parser always read it, or at the start of a line as chat
# AIs also write it: `**Resposta de referência:**`, `Resposta de Referência:`, `> - ...`, `💡 ...`,
# `**💡 ...`, `💡**...`, closing bold or italic runs of any mix (`**_..._**`).
# Never a lowercase mention in a sentence ("compare com a resposta de referência: ...").
# 💡, and ℹ️ or 1️⃣, which start with a word character; atomic, so a long run never backtracks.
EMOJI = r"(?>(?:\w\ufe0f\u20e3?|[^\w\s*_])+)"
REFERENCE_RE = re.compile(
    r"^[ \t]*(?:(?:\*|\d+[.)]|" + EMOJI + r")[ \t]+)*(?:" + EMOJI + r"(?=[*_]))?(?P<m>[*_]+)?"
    r"(?:(?:\d+[.)]|" + EMOJI + r")[^\S\n]*)?"
    r"(?i:resposta de refer[êe]ncia)"
    # The closing run mirrors the opening one or ends before a space, so the answer's own markers
    # (`__init__`, `*args`) stay; `_reference_answer` finds a closer that is not here.
    r"(?(m)(?:(?P=m):|[*_]{0,3}:[*_]{1,3}(?=\s|$)|:(?P=m)|[*_]{0,3}:)|:)"
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
    for item in (*parsed.questions, *parsed.cards):
        if len(item.label) > LABEL_MAX:
            parsed.errors.append(f"Rótulo com mais de {LABEL_MAX} caracteres: {item.label}")

    if target is not None:
        for key in ("area", "conceito", "subtema"):
            found = frontmatter.get(key)
            # Names match ignoring case (D-040), so "docker" is no news for "Docker".
            expected = _contract_name(_unquoted(getattr(target, key)))  # read as the frontmatter
            if found is not None and found.lower() != expected.lower():
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
            # Lowercase keys and plain values, as chat AIs also write `Subtema:`, `**subtema:**`,
            # `nível:` or a non-breaking hyphen in a name.
            data = {
                _without_accents(k.strip().strip("*").strip()).lower(): _contract_name(
                    _unquoted(_value(k, v))
                )
                for k, sep, v in pairs
                if sep
            }
            return data, "\n".join(lines[end + 1 :])
    return {}, text


def _value(key: str, value: str) -> str:
    # `**subtema:** Nome` leaves the key's closing marker on the value, and `**Nome**` bolds it
    # whole; `*args e **kwargs` is a name, and so is `**kwargs` after `**subtema**:`.
    value = value.strip()
    if "*" in key and not key.rstrip().endswith("*"):  # the key's bold closes after the colon
        value = value[2:].strip() if value.startswith("**") else value.removesuffix("**").strip()
    whole = len(value) > 4 and value[:2] == value[-2:] == "**" and "**" not in value[2:-2]
    return value[2:-2].strip() if whole else value


def _unquoted(value: str) -> str:
    # YAML quotes a value with a colon in it, and chat AIs often quote every value; never a name
    # that only starts and ends with quoted words (`"Since" e "for"`). An apostrophe inside a
    # word (`'Don't panic'`) is not a quote.
    quote = value[:1]
    if len(value) > 1 and quote in "\"'" and value[-1] == quote:
        inner = value[1:-1]
        if quote == "'" and re.fullmatch(r"(?:[^']|'')*", inner):
            return inner.replace("''", "'").strip()  # YAML's escape: `'Teachers'' tips'`
        if not re.search(rf"(?<!\w){quote}|{quote}(?!\w)", inner):
            return inner.strip()
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
            kind = name if (name := _contract_name(heading or "")) in KNOWN_HEADINGS else "extra"
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
    if not (marker := REFERENCE_RE.search(text)):
        return None
    answer = text[marker.end() :]
    if marker["m"] and not re.search(r"[*_]:?$", marker[0]):
        answer = _without_closer(answer, marker["m"])
    if quote := re.match(r"[ \t]*>", text[marker.start() :]):
        # An answer quoted line by line, blank lines between its paragraphs included, up to its
        # first unquoted line (code after it keeps `>>>`) or a callout of its own (`> [!ia]`).
        lines = answer.split("\n")
        for n in range(1, len(lines)):
            filled = next((line for line in lines[n:] if line.strip()), "")
            if not filled.startswith(quote[0]) or filled[len(quote[0]) :].lstrip().startswith("[!"):
                break
            lines[n] = lines[n].removeprefix(quote[0]).removeprefix(" ")
        answer = "\n".join(lines)
    return answer.strip() or None


def _without_closer(answer: str, opener: str) -> str:
    """The answer without the closer of a bold the label opened and did not close.

    Pairs the runs as Markdown does, so the closer is found after the first words (`Não.** A
    imagem`), across lines or at the end, past the answer's own bold (`**imutável**`), and keeps
    the answer's own markers (`__init__`). Inline code holds no markers.
    """
    closer = opener[::-1]
    plain = re.sub(r"`[^`\n]*`", lambda code: "x" * len(code[0]), answer)
    if answer.startswith(closer):
        return answer[len(closer) :]  # touching the answer: `:_**O molde`
    depth, pair = 1, None
    for run in re.finditer(r"[*_]+", plain):
        if run[0] not in (opener, closer):
            continue
        before, after = plain[run.start() - 1 : run.start()], plain[run.end() : run.end() + 1]
        if before.strip() == "" and after.strip():
            depth += 1
        elif before.strip() and not after.isalnum():
            depth -= 1
            if not depth:
                pair = run
                break
    # Alone before the answer (`: **` with the answer below), unless on its own line the answer
    # ends with the closer that pairs (`: _ guarda o resultado._`, about Python's `_`).
    alone = re.match(rf"[ \t]+{re.escape(closer)}(?=\s|$)", answer)
    below = alone and not answer[alone.end() :].split("\n", 1)[0].strip()
    if alone and (below or not pair or plain[pair.end() :].strip()):
        return answer[alone.end() :]
    if pair:
        return answer[: pair.start()] + answer[pair.end() :]
    # Unpaired, so the answer's own markers are literal (`**kwargs`): the closer ends the answer,
    # alone or stacked on its last markers (`__init__**`), or else it is the first one on the
    # label's line that closes a sentence (`Use **kwargs.** Ele`).
    end = len(plain.rstrip())
    if plain[:end].endswith(closer):
        return answer[: end - len(closer)] + answer[end:]
    line = plain.split("\n", 1)[0]  # a sentence end, never a word's own bold (`**imutável**`)
    if lone := re.search(rf"(?<=[.!?;:,)]){re.escape(closer)}(?![\w*_])", line):
        return answer[: lone.start()] + answer[lone.end() :]
    return answer


def _parse_cards(body: str) -> tuple[list[Card], list[str]]:
    cards: list[Card] = []
    warnings: list[str] = []
    for line in body.split("\n"):
        if match := CARD_RE.match(line):
            cards.append(Card(*match.groups()))
        elif label := CARD_LABEL_RE.match(line):
            warnings.append(
                f"Cartão {label.group(1)} sem frente ou sem '::' antes do verso, ignorado"
            )
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
# The request's last line inside the block: what follows it is chat, and its absence a cut.
# Spaces only within its own line, so a long run of blank lines is read once.
END_RE = re.compile(r"^[^\S\n]*<!--[^\S\n]*fim[^\S\n]*-->[^\S\n]*$", re.MULTILINE | re.IGNORECASE)
# What a skeleton's lines may hold besides placeholders: labels, a reference answer, a link.
SKELETON_RE = re.compile(r"\b[PC]\d+\b|resposta de refer[êe]ncia|fonte|\[!ia\]|https?://\S*", re.I)
# A heading or a line that opens in bold, as chat AIs title each document ("**Subtema 2: Camadas**",
# "**Subtema 2:** Camadas", "📘 **Subtema 2**", "2. **Camadas**").
LABEL_RE = re.compile(
    r"^\s*(#{1,6}\s|(?:\d+[.)]\s+|[^\w\s*>|`-]+\s*)?(\*\*[^*].*\*\*|__[^_\s:]*[\s:][^_]*__))"
)
FRONTMATTER_MAX = 40  # lines; the contract's frontmatter has five


def split_documents(text: str) -> tuple[list[str], list[str], bool, bool]:
    """Cut an answer into subtopic documents, each starting at a frontmatter that names it.

    Chat AIs wrap the answer in a code fence, one around everything, one per document or one
    around each frontmatter, with chat text around them. One pass pairs the fences in order, as
    the reading does: a fence opened just before a frontmatter wraps documents, its closer ends
    them, and code fences inside a document stay in it. Returns the documents, the stretches of
    text outside every document (so the screen can show what was left out), whether a wrapping
    fence never closed, the sign of an answer cut short, and whether a <!-- fim --> line followed
    the last document.
    """
    text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    documents: list[list[str]] = []
    heads: list[int] = []  # frontmatter length of each document, which trimming never cuts
    ignored: list[list[str]] = [[]]
    wrapper = None  # the fence wrapping the documents: its character and length
    chat = []  # fences open in the chat, innermost last: one may be a wrapper read late
    inner = None  # a code fence open inside a document
    outside = True
    closed = None  # how many documents a <!-- fim --> line followed, at the last one
    around = 0  # chat fences open when the last document started, which hold the documents
    seen: dict = {}  # what _heading_ahead learned
    i = 0
    while i < len(lines):
        line = lines[i]
        fence = FENCE_RE.match(line)
        if inner is None and (end := _frontmatter_end(lines, i)) is not None:
            documents.append(lines[i : end + 1])
            heads.append(end + 1 - i)
            around = len(chat)
            outside = False
            i = end + 1
            if wrapper and (closer := _closes(lines, i, wrapper)) is not None:
                # A fence around the frontmatter alone (Gemini writes ```yaml): not a wrapper.
                i, wrapper = closer + 1, None
            continue
        # The line ends the documents before it, inside the wrapper or after its closer; one in
        # a code snippet of the chat, or in the chat before any document, does not count.
        if (
            documents
            and inner is None
            and (not outside or len(chat) <= around)
            and END_RE.match(line)
        ):
            closed = len(documents)
            if not outside:
                outside = True
                ignored.append([])
                i += 1
                continue
        if fence and inner is not None:
            inner = None if fence[1][:3] == inner else inner
        elif (
            fence
            and wrapper is None
            and not _closes_chat(fence, chat)
            and _opens_documents(lines, i + 1)
        ):
            wrapper, outside = (fence[1][0], len(fence[1])), True
            ignored.append([])
            i += 1
            continue
        elif (
            fence
            and wrapper
            and _is_closer(fence, wrapper)
            and not _heading_ahead(lines, i + 1, seen)
        ):
            wrapper, outside = None, True
            ignored.append([])
            i += 1
            continue
        elif fence and not outside:
            if (
                wrapper is None
                and _closes_chat(fence, chat)
                and not _heading_ahead(lines, i + 1, seen)
            ):
                # A wrapper too far from its first frontmatter to be read at its opening.
                chat.pop()
                outside = True
                ignored.append([])
                i += 1
                continue
            inner = fence[1][:3]
        elif fence:
            chat.pop() if _closes_chat(fence, chat) else chat.append((fence[1][0], len(fence[1])))
        (ignored[-1] if outside else documents[-1]).append(line)
        i += 1

    read = []
    for n, (document, head) in enumerate(zip(documents, heads, strict=True)):
        labels = []
        while len(document) > head:
            last, plain = document[-1], document[-1].lstrip()
            if (
                LABEL_RE.match(last)
                and not contract_heading(plain)
                and not QUESTION_RE.match(plain)
                and " :: " not in last  # a card, even in bold
                # Only the answer's end can be cut, and there a bold key may open the next document.
                and not (n == len(documents) - 1 and FRONTMATTER_KEY_RE.match(last))
            ):
                labels.insert(0, last)
            elif not (last.strip() in ("", "---", "***", "___") or COMMENT_RE.match(last)):
                break
            document.pop()  # blank lines, rules and comments chat AIs put between documents
        prose = [line for line, in_fence in _outside_fences(document) if not in_fence]
        headings = [line for line in prose if contract_heading(line.lstrip())]
        whole = bool(headings) and not _skeleton(document[head:])
        read.append((document, labels, headings, whole, len(document) > head))
    real = sum(item[3] for item in read)
    texts = []
    for n, (document, labels, headings, whole, body) in enumerate(read):
        ignored.append(labels)
        cut_here = n == len(read) - 1 and closed is None and not body  # cut after a frontmatter
        if (closed is not None and n >= closed) or (real and not whole and not cut_here):
            # After the last <!-- fim --> line, or beside a real document a header or a skeleton
            # of the format, which the chat shows as an example: never a document. The import
            # blocks on it as content left out.
            ignored.append(document)
            continue
        # A document nested in a list item: its opening `---` and every contract heading share
        # an indentation, which the parser reads from the margin. A frontmatter indented alone
        # leaves the body as written.
        indent = document[0][: len(document[0]) - len(document[0].lstrip())]
        if indent and headings and all(line.startswith(indent) for line in headings):
            document = _dedented(document, indent)
        texts.append("\n".join(document) + "\n")
    stretches = ("\n".join(stretch).strip() for stretch in ignored)
    cut = wrapper is not None or (bool(chat) and not outside)
    # A real document after the last line: the AI ended each one with it, and the last was cut.
    ended = closed is not None and not any(item[3] for item in read[closed:])
    return texts, [stretch for stretch in stretches if stretch], cut, ended


def _skeleton(body: list[str]) -> bool:
    """Whether every section opens with a placeholder (`...`, `- C1: ... :: ...`): a format shown.

    Only the first line counts, so the chat after the last section does not make it a document.
    """
    opening = False
    for line in body:
        if contract_heading(line.lstrip()):
            opening = True
        elif opening and line.strip() and not FENCE_RE.match(line):
            if re.search(r"\w", SKELETON_RE.sub("", line)):
                return False
            opening = False
    return True


def _dedented(lines: list[str], indent: str) -> list[str]:
    """The lines without `indent`, but a code block loses only what all its filled lines share, so
    code written at the margin keeps its own nesting."""
    out, code, fence = [], [], None

    def flush():
        cut = len(os.path.commonprefix([indent, *(line for line in code if line.strip())]))
        out.extend(line[cut:] for line in code)
        code.clear()

    for line in lines:
        marker = _fence_marker(line)
        if fence and marker != fence:
            code.append(line)
            continue
        flush()
        fence = None if fence else marker
        out.append(line.removeprefix(indent))
    flush()  # a code block the document never closed
    return out


def _frontmatter_end(lines: list[str], start: int, chained: bool = True) -> int | None:
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
            if "subtema" not in keys:
                return None
            # A closer that opens a whole frontmatter of its own: this one was cut, and the answer
            # restarted the document after it.
            return None if chained and _frontmatter_end(lines, end, False) is not None else end
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
        if (
            start >= len(lines)
            or FENCE_RE.match(lines[start])
            or contract_heading(lines[start].lstrip())
        ):
            return False
        start += 1
    return False


def _heading_ahead(lines: list[str], start: int, seen: dict) -> bool:
    """Whether the document goes on after the code the fence at `start - 1` would open.

    Inside a ``` wrapper, a bare ``` may open an example as well as close the wrapper. Code it
    opens ends at the next bare fence, and then a contract heading must follow before the next
    frontmatter, outside any later code block: a chat heading ("## Próximos passos") or one in a
    chat snippet after the wrapper does not keep it open. `seen` keeps the answer of each line
    read after that code, so a run of fences is read once.
    """
    inner, fence = True, None  # in the code the fence would open; in a later code block
    path = []  # the states after the code, which all lead to this answer
    for at in range(start, len(lines)):
        state = (at, fence is None)
        if not inner:
            if state in seen:
                result = seen[state]
                break
            path.append(state)
        if fence is None and _frontmatter_end(lines, at) is not None:
            result = False
            break
        found = FENCE_RE.match(lines[at])
        if found and inner:
            if found[2].strip():
                return False  # a fence with a language opens code, it cannot end it
            inner = False
        elif found:
            fence = None if fence else found[1]
        elif not inner and fence is None and contract_heading(lines[at].lstrip()):
            result = True
            break
    else:
        result = False
    seen.update(dict.fromkeys(path, result))
    return result


def contract_heading(line: str) -> bool:
    return line.startswith("## ") and _contract_name(line[3:]) in KNOWN_HEADINGS


def _contract_name(heading: str) -> str:
    # Chat AIs may write a non-breaking hyphen (U+2011) in "Pré-requisitos".
    return heading.strip().replace("\u2011", "-").replace("\u2010", "-")


def _next_filled(lines: list[str], start: int) -> int:
    while start < len(lines) and not lines[start].strip():
        start += 1
    return start


def _is_closer(fence, wrapper) -> bool:
    return not fence[2].strip() and fence[1][0] == wrapper[0] and len(fence[1]) >= wrapper[1]


def _closes_chat(fence, chat) -> bool:
    return bool(chat) and _is_closer(fence, chat[-1])


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
    if not parsed.frontmatter.get("nivel"):  # an unknown one already warns
        gaps.append("O frontmatter não diz o nivel")
    if not any(b.kind == "Fontes" and "http" in b.body for b in parsed.blocks):
        gaps.append("Fontes sem nenhum link")
    for block in (b for b in parsed.blocks if b.kind == "Prática"):
        odd, orphan, between, answer, label = [], [], [], False, None
        for line, in_fence in _outside_fences(block.body.split("\n")):
            if not in_fence and (question := QUESTION_RE.match(line)):
                answer, label = False, question[1]
                continue
            if label and not answer and line.strip() and not REFERENCE_RE.search(line):
                between.append(label)
            if in_fence:
                continue
            # A label opening the line, or right after a question in another format; not an intro.
            if label is None and (found := REFERENCE_RE.search(line)):
                before = line[: found.start()]
                # Read backwards, so a long run of marks is scanned once.
                if not before.strip() or "?" in re.match(r"[\W_]*", before[::-1])[0]:
                    orphan.append(line)  # its question is in another format: the reading shows it
            # An answer may have its own sub-headings (`#### Passo 1`), never a question's level.
            heading = HEADING_RE.match(line) and (not answer or line.startswith("### "))
            if QUESTION_LIKE_RE.match(line) or heading:
                odd.append(line)
            answer = answer or bool(REFERENCE_RE.search(line))
        if odd:
            gaps.append(f"Pergunta fora do formato ### P1: ...: {odd[0].strip()[:80]}")
        if orphan:
            gaps.append(
                "Resposta de referência antes da primeira pergunta ### P1: ...: "
                f"{orphan[0].strip()[:80]}"
            )
        if between:
            # Practice shows only the question's line (spec 4.2.4): code under it would be lost.
            gaps.append(
                f"Texto entre ### {between[0]} e a resposta de referência: a Prática mostra só a "
                "linha da pergunta"
            )
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
        stray, callout = [], False
        for raw in block.body.split("\n"):
            line = raw.strip()
            # A `> [!ia]` callout may sit anywhere; anything else here would vanish from the cards.
            callout = line.startswith("> [!ia]") or (callout and line.startswith(">"))
            if callout and not CARD_LABEL_RE.match(line.lstrip("> ")):
                continue  # a quoted card, even in a callout, is never read as one
            if not line or (CARD_LABEL_RE.match(raw) and not CARD_RE.match(raw)):
                continue  # empty, or a label without `::`, which already warns
            if CARD_RE.match(raw):
                # The parser cuts at the first `::`: one in code (`std::vector`, `[::2]`) or a
                # second spaced one means the front may end in the wrong place.
                before, _, after = raw.partition("::")
                if not (before[-1:].isspace() and after[:1].isspace()) or " :: " in after:
                    gaps.append(f"Cartão com '::' fora do separador ' :: ': {line[:80]}")
            else:
                stray.append(line)
        if stray:
            gaps.append(f"Linha em Flashcards fora do formato - C1: ... :: ...: {stray[0][:80]}")
    if "Flashcards" in kinds and not parsed.cards:
        gaps.append("Nenhum cartão em Flashcards")
    return gaps
