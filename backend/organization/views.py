from django.db import transaction
from django.db.models import ProtectedError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Area, Concept, Settings, Step, Subtopic, Track
from .serializers import (
    AreaSerializer,
    ConceptSerializer,
    SettingsSerializer,
    StepSerializer,
    SubtopicDetailSerializer,
    SubtopicSerializer,
    TrackSerializer,
)

# Prefetching subtopics lets the derived concept status skip one query per concept.
TRACKS = Track.objects.prefetch_related("steps__concept__area", "steps__concept__subtopics")


class ProtectedDeleteMixin:
    """A parent that still has children is never deleted: nothing is erased silently."""

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Isto ainda tem itens dentro. Remova-os antes."},
                status=status.HTTP_409_CONFLICT,
            )


class AreaViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer


class ConceptViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = Concept.objects.select_related("area").prefetch_related("subtopics")
    serializer_class = ConceptSerializer


class SubtopicViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = Subtopic.objects.all()

    def get_serializer_class(self):
        return SubtopicSerializer if self.action == "list" else SubtopicDetailSerializer

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        return self._change_status(services.complete_subtopic)

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        return self._change_status(services.reopen_subtopic)

    def _change_status(self, change):
        subtopic = self.get_object()
        try:
            change(subtopic)
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(subtopic).data)


class TrackViewSet(viewsets.ModelViewSet):
    queryset = TRACKS
    serializer_class = TrackSerializer


class StepViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Step.objects.select_related("concept__area")
    serializer_class = StepSerializer

    @action(detail=True, methods=["post"])
    def move(self, request, pk=None):
        direction = request.data.get("direction")
        if direction not in ("up", "down"):
            return Response(
                {"direction": ['Use "up" ou "down".']}, status=status.HTTP_400_BAD_REQUEST
            )
        with transaction.atomic():
            step = self.get_object()
            Track.objects.select_for_update().get(pk=step.track_id)
            steps = list(Step.objects.filter(track_id=step.track_id))
            index = next(i for i, s in enumerate(steps) if s.pk == step.pk)
            other = index - 1 if direction == "up" else index + 1
            if 0 <= other < len(steps):
                steps[index], steps[other] = steps[other], steps[index]
            # Renumber the whole track so gaps left by removed steps never matter.
            for position, s in enumerate(steps):
                s.order = position
            Step.objects.bulk_update(steps, ["order"])
        track = TRACKS.get(pk=step.track_id)
        return Response(TrackSerializer(track).data)


class SettingsView(APIView):
    def get(self, request):
        return Response(SettingsSerializer(Settings.load()).data)

    def patch(self, request):
        serializer = SettingsSerializer(Settings.load(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
