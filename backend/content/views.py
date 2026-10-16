from dataclasses import asdict

from activity.services import review_cap_today
from django.shortcuts import get_object_or_404
from organization.models import Subtopic
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Content, Flashcard
from .parser import Target, parse_markdown
from .serializers import (
    ContentSerializer,
    FlashcardSerializer,
    MarkdownSerializer,
    RatingSerializer,
)
from .services import (
    approve_card,
    import_content,
    rate_card,
    reject_card,
    review_queue,
    reviews_today,
)


def _parse_request(request, subtopic):
    serializer = MarkdownSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    concept = subtopic.concept
    target = Target(area=concept.area.name, conceito=concept.name, subtema=subtopic.name)
    return parse_markdown(serializer.validated_data["markdown"], target)


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
        import_content(subtopic, parsed)
        return Response(ContentSerializer(subtopic.content).data)


class ContentPreviewView(APIView):
    """Parses without saving anything."""

    def post(self, request, pk):
        return Response(_preview(_parse_request(request, _subtopic(pk))))


class FlashcardViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = FlashcardSerializer

    def get_queryset(self):
        cards = Flashcard.objects.all()
        if subtopic := self.request.query_params.get("subtopic"):
            cards = cards.filter(subtopic_id=subtopic)
        if state := self.request.query_params.get("state"):
            cards = cards.filter(state=state)
        return cards

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._decide(approve_card)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._decide(reject_card)

    @action(detail=True, methods=["post"])
    def rate(self, request, pk=None):
        serializer = RatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._decide(lambda card: rate_card(card, serializer.validated_data["rating"]))

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
