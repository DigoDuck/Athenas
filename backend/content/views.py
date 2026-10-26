from dataclasses import asdict

from activity.services import review_cap_today
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from organization.models import Subtopic
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Content, Flashcard, Image
from .parser import Target, parse_markdown
from .serializers import (
    ContentSerializer,
    FlashcardSerializer,
    ImageUploadSerializer,
    ManualCardSerializer,
    MarkdownSerializer,
    ThemeSerializer,
)
from .services import (
    approve_card,
    create_manual_card,
    import_content,
    import_theme,
    reject_card,
    review_queue,
    reviews_today,
    save_image,
)


def _parse_request(request, subtopic):
    serializer = MarkdownSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    concept = subtopic.concept
    target = Target(area=concept.area.name, conceito=concept.name, subtema=subtopic.name)
    parsed = parse_markdown(serializer.validated_data["markdown"], target)
    stored = set(Image.objects.filter(name__in=parsed.images).values_list("name", flat=True))
    parsed.warnings += [f"Imagem não encontrada: {n}" for n in parsed.images if n not in stored]
    return parsed


def _preview(parsed):
    data = asdict(parsed)
    data.pop("raw")
    for item, callout in zip(data["callouts"], parsed.callouts, strict=True):
        item["unsourced"] = callout.unsourced
    return data


def _subtopic(pk):
    return get_object_or_404(Subtopic.objects.select_related("concept__area"), pk=pk)


class ContentView(APIView):
    """The subtopic's Markdown: read it, or save it (spec 4.2.1)."""

    def get(self, request, pk):
        content = get_object_or_404(Content, subtopic_id=pk)
        return Response(ContentSerializer(content).data)

    def put(self, request, pk):
        subtopic = _subtopic(pk)
        parsed = _parse_request(request, subtopic)
        if parsed.errors:
            # Duplicate labels block the save (spec 4.2.7).
            return Response(_preview(parsed), status=status.HTTP_400_BAD_REQUEST)
        # `base` is the saved text the editor started from (null: none); theme.py sends none.
        stored = Content.objects.filter(subtopic=subtopic).values_list("raw_markdown", flat=True)
        if "base" in request.data and request.data["base"] != stored.first():
            return Response(
                {
                    "detail": "O conteúdo salvo mudou depois que você abriu o editor. Seu texto "
                    "continua aqui; salve de novo para substituir o que está salvo.",
                    "raw_markdown": stored.first(),
                },
                status=status.HTTP_409_CONFLICT,
            )
        import_content(subtopic, parsed)
        return Response(ContentSerializer(subtopic.content).data)


class ContentPreviewView(APIView):
    """Parses without saving anything."""

    def post(self, request, pk):
        return Response(_preview(_parse_request(request, _subtopic(pk))))


class ThemeView(APIView):
    """A pasted AI answer: `preview/` reports, the bare path creates (D-040)."""

    save = True

    def post(self, request):
        serializer = ThemeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = import_theme(**serializer.validated_data, save=self.save)
        if not self.save:
            return Response(report)
        if "track" not in report:
            return Response(report, status=status.HTTP_400_BAD_REQUEST)
        return Response(report, status=status.HTTP_201_CREATED)


class ImageView(APIView):
    """One stored image: its bytes, or an upload that creates or replaces it (D-033)."""

    def get(self, request, name):
        image = get_object_or_404(Image, name=name)
        response = HttpResponse(bytes(image.data), content_type=image.media_type)
        # An SVG opened on its own must not run scripts or fetch anything: it is shown offline.
        response["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'"
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "no-cache"
        return response

    def put(self, request, name):
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            created = save_image(name, **serializer.validated_data)
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"name": name}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class FlashcardViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = FlashcardSerializer

    def get_queryset(self):
        cards = Flashcard.objects.all()
        if subtopic := self.request.query_params.get("subtopic"):
            if not subtopic.isdigit():
                raise ValidationError({"subtopic": "Informe o id do subtema."})
            cards = cards.filter(subtopic_id=subtopic)
        if state := self.request.query_params.get("state"):
            cards = cards.filter(state=state)
        return cards

    def create(self, request):
        """Manual cards only; Markdown cards come from importing the content."""
        serializer = ManualCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            card = create_manual_card(**serializer.validated_data)
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(FlashcardSerializer(card).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._decide(approve_card)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._decide(reject_card)

    def _decide(self, decide):
        card = self.get_object()
        try:
            decide(card)
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_409_CONFLICT)
        return Response(FlashcardSerializer(card).data)


class ReviewTodayView(APIView):
    """Today's queue within the caps, and the home screen's N; never overdue totals (4.6.4)."""

    def get(self, request):
        # A return session offers at most 5 reviews; they count toward the day's cap (4.7).
        cap = review_cap_today()
        cards = FlashcardSerializer(review_queue(cap=cap), many=True).data
        return Response({"count": reviews_today(cap=cap), "cards": cards})
