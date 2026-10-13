"""Pure parser for the subtopic Markdown contract (spec 4.1 and 4.2). No Django, no database."""

import re
import unicodedata
from dataclasses import dataclass, field

KNOWN_HEADINGS = {
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
}

QUESTION_RE = re.compile(r"^###\s+(P\d+):\s*(.+?)\s*$")
CARD_RE = re.compile(r"^-\s+(C\d+):\s*(.+?)\s*::\s*(.+?)\s*$")
CARD_LABEL_RE = re.compile(r"^-\s+(C\d+):")
SOURCE_RE = re.compile(r"Fonte:\s*(https?://\S+)")
REFERENCE_PREFIX = "Resposta de referência:"
# Stored without accents, like `Subtopic.Level` ("intermediário" -> "intermediario").
LEVELS = {"iniciante", "intermediario", "avancado", "especialista"}


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


@dataclass
class ParsedContent:
    raw: str = field(default="", compare=False)  # as pasted; "parses the same" ignores it
    level: str | None = None
    frontmatter: dict[str, str] = field(default_factory=dict)
    blocks: list[Block] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)
    cards: list[Card] = field(default_factory=list)
    callouts: list[Callout] = field(default_factory=list)
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

    for label in _duplicates([q.label for q in parsed.questions]):
        parsed.errors.append(f"Rótulo duplicado: {label}")
    for label in _duplicates([c.label for c in parsed.cards]):
        parsed.errors.append(f"Rótulo duplicado: {label}")

    if target is not None:
        for key in ("area", "conceito", "subtema"):
            found = frontmatter.get(key)
            if found is not None and found != getattr(target, key):
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
            data = {k.strip(): v.strip() for k, sep, v in pairs if sep}
            return data, "\n".join(lines[end + 1 :])
    return {}, text


def _outside_fences(lines):
    """Yield (line, in_fence) so a `##` inside a fenced code block is never a heading."""
    fence = None
    for line in lines:
        marker = line.lstrip()[:3]
        if marker in ("```", "~~~"):
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
    _, sep, rest = "\n".join(lines).partition(REFERENCE_PREFIX)
    return (rest.strip() or None) if sep else None


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
    callouts: list[Callout] = []
    current: list[str] | None = None

    def close():
        if current is not None:
            text = "\n".join(current)
            source = SOURCE_RE.search(text)
            callouts.append(Callout(text, source.group(1) if source else None))

    for line, in_fence in _outside_fences(body.split("\n")):
        stripped = line.strip()
        if not in_fence and stripped.startswith("> [!ia]"):
            close()
            current = [stripped[1:].strip()]
        elif current is not None and not in_fence and stripped.startswith(">"):
            current.append(stripped[1:].strip())
        else:
            close()
            current = None
    close()
    return callouts


def _duplicates(labels: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: list[str] = []
    for label in labels:
        if label in seen and label not in dupes:
            dupes.append(label)
        seen.add(label)
    return dupes
