"""Re-import of a parsed document into a subtopic. Identity follows the labels (spec 4.2.6)."""

import itertools
import re
from collections import defaultdict
from datetime import UTC, datetime, time, timedelta

import fsrs
from django.db import connection, transaction
from django.db.models import Min
from django.utils import timezone
from organization.models import Area, Concept, Settings, Step, Track
from organization.serializers import StepSerializer, SubtopicSerializer

from . import images
from .models import Block, Content, Flashcard, Image, PracticeQuestion, ReviewLog
from .parser import (
    FRONTMATTER_KEY_RE,
    ParsedContent,
    Target,
    contract_gaps,
    contract_heading,
    parse_markdown,
    reading_key,
    split_documents,
    with_origin,
)


@transaction.atomic
def import_content(subtopic, parsed: ParsedContent) -> None:
    if parsed.errors:
        raise ValueError("; ".join(parsed.errors))
    _save_content(subtopic, parsed)
    _sync_questions(subtopic, parsed)
    _sync_cards(subtopic, parsed)
    if parsed.level is not None:
        subtopic.level = parsed.level
        subtopic.save(update_fields=["level"])


def _save_content(subtopic, parsed):
    content, _ = Content.objects.update_or_create(
        subtopic=subtopic,
        defaults={
            "raw_markdown": parsed.raw,
            "state": parsed.state,
            "generated_by": parsed.generated_by,
        },
    )
    # A block with identical kind, heading and body keeps its read mark (DECISIONS.md D-015);
    # adding or moving an image line does not change the body it compares (D-033).
    read = defaultdict(list)
    for old in content.blocks.exclude(read_at=None):
        read[(old.kind, old.heading, reading_key(old.body))].append(old.read_at)
    content.blocks.all().delete()
    blocks = []
    for order, block in enumerate(parsed.blocks):
        marks = read[(block.kind, block.heading, reading_key(block.body))]
        blocks.append(
            Block(
                content=content,
                order=order,
                kind=block.kind,
                heading=block.heading,
                body=block.body,
                read_at=marks.pop() if marks else None,
            )
        )
    Block.objects.bulk_create(blocks)


def _sync_questions(subtopic, parsed):
    existing = {q.label: q for q in subtopic.questions.all()}
    for item in parsed.questions:
        values = {"prompt": item.prompt, "reference_answer": item.reference_answer or ""}
        PracticeQuestion.objects.update_or_create(
            subtopic=subtopic, label=item.label, defaults={**values, "archived": False}
        )
    kept = {item.label for item in parsed.questions}
    for label, question in existing.items():
        if label not in kept and not question.archived:
            question.archived = True
            question.save(update_fields=["archived"])


def _sync_cards(subtopic, parsed):
    # Manual cards have no label and are not in the Markdown: a re-import never suspends them.
    existing = {c.label: c for c in subtopic.flashcards.filter(origin=Flashcard.Origin.MARKDOWN)}
    for item in parsed.cards:
        card = existing.get(item.label)
        if card is None:
            card = Flashcard.objects.create(
                subtopic=subtopic, label=item.label, front=item.front, back=item.back
            )
            start_fsrs_state(card)
            continue
        card.front, card.back = item.front, item.back
        if card.state == Flashcard.State.SUSPENDED:
            card.state = card.state_before_suspension or Flashcard.State.PENDING
            card.state_before_suspension = ""
        card.save()
    kept = {item.label for item in parsed.cards}
    for label, card in existing.items():
        if label not in kept and card.state != Flashcard.State.SUSPENDED:
            # A rejected label that leaves and comes back starts over as pending (spec 4.3.4).
            rejected = card.state == Flashcard.State.REJECTED
            card.state_before_suspension = Flashcard.State.PENDING if rejected else card.state
            card.state = Flashcard.State.SUSPENDED
            card.save()


# "Novo tema" (DECISIONS.md D-040): one pasted AI answer becomes concepts and subtopics in a track.

NAME_MAX = 160  # Concept.name and Subtopic.name
FRONTMATTER_KEYS = {"area", "conceito", "subtema", "nivel", "origem"}
THEME_LOCK = 4045  # any constant: the advisory lock key for saving a round
KEPT = (
    "O subtema já tem outro texto, que fica como está. Para trocar, cole este documento no "
    "subtema, na Biblioteca."
)
NO_DOCUMENT = (
    "Nenhum documento encontrado. Cada subtema começa pelo frontmatter: uma linha ---, as linhas "
    "area, conceito e subtema, e outra linha ---. Copie a resposta pelo botão de copiar do bloco "
    "de código, não selecionando o texto."
)


@transaction.atomic
def import_theme(*, area, track, origem, markdown, save=False) -> dict:
    """What the answer would create, and with `save` creates it, all or nothing.

    Area and track come from the screen; each document names its concept and subtopic. Names
    match what exists ignoring case, so a round never duplicates a row. Only what is missing is
    created: a subtopic that already has other text keeps it, like `scripts/theme.py push`
    without `--replace`, so nothing Diogo edited or studied changes here.
    """
    if save:
        # One round at a time: a second save of the same answer waits, then finds it done.
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [THEME_LOCK])
    documents, ignored, cut = split_documents(markdown)
    area_obj = Area.objects.filter(name__iexact=area).first()
    track_obj = Track.objects.filter(name__iexact=track).first()
    report = {
        "area_new": area_obj is None,
        "track_new": track_obj is None,
        "complete": False,
        "documents": [],
        "warnings": [],
        "errors": [],
    }
    if not documents:
        # Chat AIs add bold, a period or a sentence around it: "Claro!\n\n**TRILHA COMPLETA**".
        # Never a heading: "## Trilha completa" titles a plan.
        report["complete"] = any(
            # Bold, a period, an emoji go; a colon, a question or a list marker make it a title.
            re.sub(r"[^\w\s:?|-]", "", line).strip().upper() == "TRILHA COMPLETA"
            for line in markdown.split("\n")
            if not re.match(r"\s*(#|[*+]\s)", line)
        )
        report["errors"].append(
            "A IA respondeu que a trilha está completa." if report["complete"] else NO_DOCUMENT
        )
        return report
    for stretch in ignored:
        # A contract heading, or a `---` with a `subtema` key, outside every document is content
        # the split lost; a chat line such as "**Subtema:** Volumes" is not.
        lines = stretch.split("\n")
        lost = (
            any(contract_heading(line) for line in lines)
            or _open_frontmatter(lines)
            or (
                any(line.strip() == "---" for line in lines)
                and any(
                    (k := FRONTMATTER_KEY_RE.match(line)) and k[1].lower() == "subtema"
                    for line in lines
                )
            )
        )
        report["errors" if lost else "warnings"].append(
            f"Um trecho com títulos ficou fora dos documentos: {_excerpt(stretch)}. Confira se a "
            "resposta veio inteira, no formato pedido."
            if lost
            else f"Texto fora dos documentos, ignorado: {_excerpt(stretch)}"
        )

    plans, seen = [], set()
    for text in documents:
        text = with_origin(text, origem)
        names = parse_markdown(text).frontmatter
        conceito, subtema = names.get("conceito", ""), names.get("subtema", "")
        parsed = parse_markdown(text, Target(area, conceito, subtema))
        errors = _document_errors(parsed, conceito, subtema)
        if (conceito.lower(), subtema.lower()) in seen:
            errors.append(f"Subtema repetido na resposta: {conceito} / {subtema}")
        seen.add((conceito.lower(), subtema.lower()))
        concept = area_obj and area_obj.concepts.filter(name__iexact=conceito).first()
        subtopic = concept and concept.subtopics.filter(name__iexact=subtema).first()
        stored = Content.objects.filter(subtopic=subtopic).first() if subtopic else None
        action = "create" if subtopic is None else "fill" if stored is None else "keep"
        warnings = parsed.warnings + contract_gaps(parsed)
        if action == "keep" or (stored and stored.raw_markdown == parsed.raw):
            # Never imported, so problems in its own text cannot block; a broken split still does.
            warnings = parsed.errors + warnings
        else:
            errors = parsed.errors + errors
        if stored and stored.raw_markdown == parsed.raw:
            action = "same"
        elif action == "keep":
            warnings.append(KEPT)
        joins_track = ""
        if concept and not concept.steps.filter(track=track_obj).exists():
            others = ", ".join(concept.steps.values_list("track__name", flat=True))
            joins_track = (
                f"O conceito {concept.name} já existe nesta área"
                + (f", na trilha {others}" if others else "")
                + ": os subtemas entram nele, e ele entra também nesta trilha."
            )
            warnings.append(joins_track)
        found = set(Image.objects.filter(name__in=parsed.images).values_list("name", flat=True))
        warnings += [f"Imagem não encontrada: {n}" for n in parsed.images if n not in found]
        plans.append((parsed, conceito, subtema, action))
        report["documents"].append(
            {
                "conceito": conceito,
                "subtema": subtema,
                "concept_new": concept is None,
                # An existing concept this round adds to the track, even with no new subtopic: the
                # note that says so, which is not a problem for the AI to fix.
                "joins_track": joins_track,
                "action": action,
                "state": parsed.state,
                "level": parsed.level,
                "generated_by": parsed.generated_by,
                "questions": len(parsed.questions),
                "cards": len(parsed.cards),
                "unsourced": sum(c.unsourced for c in parsed.callouts),
                "warnings": warnings,
                "errors": errors,
            }
        )
    if cut:
        report["documents"][-1]["warnings"].append(
            "O bloco de código da resposta não fechou: ela pode ter sido cortada. Confira o fim "
            "deste documento."
        )
    blocked = report["errors"] or any(d["errors"] for d in report["documents"])
    if not save or blocked:
        return report

    area_obj = area_obj or Area.objects.create(name=area)
    track_obj = track_obj or Track.objects.create(name=track)
    pending = 0
    for parsed, conceito, subtema, action in plans:
        concept = area_obj.concepts.filter(name__iexact=conceito).first()
        concept = concept or Concept.objects.create(area=area_obj, name=conceito)
        if not Step.objects.filter(track=track_obj, concept=concept).exists():
            _create(StepSerializer, track=track_obj.pk, concept=concept.pk)
        if action in ("keep", "same"):
            continue
        subtopic = concept.subtopics.filter(name__iexact=subtema).first()
        subtopic = subtopic or _create(SubtopicSerializer, concept=concept.pk, name=subtema)
        import_content(subtopic, parsed)
        pending += len(parsed.cards)
    report |= {"track": track_obj.pk, "pending": pending}
    return report


def _document_errors(parsed, conceito, subtema):
    errors = []
    if not conceito or not subtema:
        errors.append("O frontmatter precisa de conceito e subtema")
    if len(conceito) > NAME_MAX or len(subtema) > NAME_MAX:
        errors.append(f"Nome de conceito ou subtema com mais de {NAME_MAX} caracteres")
    if any(name.startswith("<") and name.endswith(">") for name in (conceito, subtema)):
        errors.append(
            "Nome entre < e >: é o modelo do pedido, não um nome. Troque pelo nome real, ou "
            "apague o trecho se a IA só repetiu o modelo."
        )
    if not parsed.blocks:
        errors.append("Documento sem texto depois do frontmatter: a resposta foi cortada?")
    if _open_frontmatter(parsed.raw.split("\n")):
        errors.append("O documento termina num frontmatter que não fechou: a resposta foi cortada?")
    kinds = [block.kind for block in parsed.blocks if block.kind != "extra"]
    for kind in dict.fromkeys(k for k in kinds if kinds.count(k) > 1):
        # Two documents run together when the second frontmatter was not recognized.
        errors.append(f"A seção {kind} aparece mais de uma vez: dois documentos se juntaram?")
    return errors


def _open_frontmatter(lines):
    """Whether the lines end in the next document's frontmatter, cut before its closing `---`.

    Its keys follow the last rule: one is `subtema`, or all are frontmatter keys with `area` first
    as the request asks, the last one maybe cut in the middle of its name.
    """
    tail = list(itertools.takewhile(lambda ln: ln.strip() != "---", reversed(lines)))
    filled = [line for line in reversed(tail) if line.strip()]
    if len(tail) == len(lines) or not filled:
        return False  # no rule, or nothing after it
    if len(filled) > 1 and re.fullmatch(r"\s*\**[\w-]+", filled[-1]):
        filled.pop()
    keys = [FRONTMATTER_KEY_RE.match(line) for line in filled]
    if not all(keys):
        return False
    names = [k[1].lower() for k in keys]
    return "subtema" in names or (names[0] == "area" and set(names) <= FRONTMATTER_KEYS)


def _create(serializer_class, **data):
    # Reuses the serializers' append-at-the-end ordering, with its row lock.
    serializer = serializer_class(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.save()


def _excerpt(text, size=80):
    line = " ".join(text.split())
    return f"«{line[:size]}…»" if len(line) > size else f"«{line}»"


def save_image(name, data, **credit) -> bool:
    """Store or replace the image called `name`; True when it is new (D-033)."""
    if not images.NAME_RE.fullmatch(name):
        raise ValueError(f"Nome de imagem inválido: {name}; use letras minúsculas, números e -")
    if found := images.problems(data, **credit):
        raise ValueError("; ".join(found))
    _, created = Image.objects.update_or_create(
        name=name, defaults={"data": data, "media_type": images.media_type(data), **credit}
    )
    return created


def approve_card(card) -> None:
    """Pending becomes active and new; the new card cap applies to it (spec 4.3.3)."""
    _decide(card, Flashcard.State.ACTIVE)


def reject_card(card) -> None:
    _decide(card, Flashcard.State.REJECTED)


@transaction.atomic
def create_manual_card(*, front, back, subtopic=None, concept=None) -> Flashcard:
    """On a subtopic or on a concept, never both; Diogo's own, so active (spec 4.3.5, Q6)."""
    if (subtopic is None) == (concept is None):
        raise ValueError("Escolha um subtema ou um conceito, não os dois.")
    card = Flashcard.objects.create(
        origin=Flashcard.Origin.MANUAL,
        subtopic=subtopic,
        concept=concept,
        front=front,
        back=back,
        state=Flashcard.State.ACTIVE,
    )
    start_fsrs_state(card)
    return card


def _decide(card, state):
    # One card at a time, and only a pending one: there is no "approve all" (spec 4.3.2).
    if card.state != Flashcard.State.PENDING:
        raise ValueError(f"O cartão {card.label} não está pendente")
    card.state = state
    card.save(update_fields=["state"])


# Review scheduling (spec 4.6, DECISIONS.md D-011, D-018 and D-022).

FSRS_RATINGS = {
    ReviewLog.Rating.AGAIN: fsrs.Rating.Again,
    ReviewLog.Rating.HARD: fsrs.Rating.Hard,
    ReviewLog.Rating.GOOD: fsrs.Rating.Good,
}


def start_fsrs_state(card) -> None:
    """Every card starts as a new Py-FSRS card keyed by its pk, whatever its approval state."""
    _store_fsrs_state(card, fsrs.Card(card_id=card.pk, due=_utc(None)))


@transaction.atomic
def rate_card(card, rating, *, now=None, enable_fuzzing=True) -> ReviewLog:
    """Again, Hard or Good through Py-FSRS; there is no Easy (spec 4.6.2)."""
    if card.state != Flashcard.State.ACTIVE:
        raise ValueError(f"O cartão {card} não está ativo")
    if rating not in ReviewLog.Rating.values:
        raise ValueError(f"Avaliação inválida: {rating}")
    rating = ReviewLog.Rating(rating)
    reviewed_at = _utc(now)
    fsrs_card, fsrs_log = _scheduler(enable_fuzzing).review_card(
        fsrs.Card.from_dict(card.fsrs_card), FSRS_RATINGS[rating], review_datetime=reviewed_at
    )
    _store_fsrs_state(card, fsrs_card)
    return ReviewLog.objects.create(
        flashcard=card, rating=rating, reviewed_at=reviewed_at, fsrs_log=fsrs_log.to_dict()
    )


def review_queue(*, now=None, cap=None) -> list[Flashcard]:
    """Today's cards: same-day repeats first, then new cards, then due cards.

    `cap` lowers the review cap for the day, as the return session does (spec 4.7).
    """
    repeats, picks = _today(now, cap)
    return repeats + picks


def reviews_today(*, now=None, cap=None) -> int:
    """The home screen's N: cards still to see today, never same-day repeats (D-022)."""
    return len(_today(now, cap)[1])


def _today(now, cap):
    now = _utc(now)
    start = timezone.make_aware(datetime.combine(timezone.localdate(now), time.min))
    end = start + timedelta(days=1)
    settings = Settings.load()
    active = Flashcard.objects.filter(state=Flashcard.State.ACTIVE)

    logs_today = ReviewLog.objects.filter(reviewed_at__gte=start, reviewed_at__lt=end)
    seen_today = set(logs_today.values_list("flashcard_id", flat=True))
    introduced_today = (
        ReviewLog.objects.values("flashcard_id")
        .annotate(first=Min("reviewed_at"))
        .filter(first__gte=start, first__lt=end)
        .count()
    )
    # The review cap counts distinct cards per Bahia day (Q14); new cards take slots first.
    review_cap = settings.review_cap if cap is None else min(cap, settings.review_cap)
    free = max(review_cap - len(seen_today), 0)
    new_slots = min(max(settings.new_card_cap - introduced_today, 0), free)
    new = list(active.filter(reviews__isnull=True).order_by("id")[:new_slots])

    due = active.filter(reviews__isnull=False, due__lt=end).exclude(id__in=seen_today).distinct()
    scheduler = _scheduler()

    def retrievability(card):
        return scheduler.get_card_retrievability(fsrs.Card.from_dict(card.fsrs_card), now)

    # Overflow stays due with its stored date untouched and competes again tomorrow (D-011).
    due = sorted(due, key=lambda card: (retrievability(card), card.id))[: free - len(new)]
    repeats = list(active.filter(id__in=seen_today, due__lte=now).order_by("due", "id"))
    return repeats, new + due


def _scheduler(enable_fuzzing=True):
    return fsrs.Scheduler(
        desired_retention=Settings.load().desired_retention, enable_fuzzing=enable_fuzzing
    )


def _store_fsrs_state(card, fsrs_card):
    # The only writer of `fsrs_card` and `due`, so the two never drift apart (D-018).
    card.fsrs_card = fsrs_card.to_dict()
    card.due = fsrs_card.due
    card.save(update_fields=["fsrs_card", "due"])


def _utc(now):
    # Py-FSRS refuses datetimes that are not in UTC.
    return (now or timezone.now()).astimezone(UTC)
