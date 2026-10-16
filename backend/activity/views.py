from content.models import Block
from content.serializers import BlockSerializer
from django.shortcuts import get_object_or_404
from organization.models import Subtopic
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SessionEvent
from .serializers import SessionEventSerializer
from .services import complete_activity, resume_block_order, start_activity


class SessionEventViewSet(viewsets.GenericViewSet):
    """Start and complete activities. No list, update or delete: events are history."""

    queryset = SessionEvent.objects.all()
    serializer_class = SessionEventSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            event = start_activity(**serializer.validated_data)
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(event).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        event = self.get_object()
        try:
            complete_activity(event)
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(event).data)


class ReadingView(APIView):
    """The blocks in document order and where reading resumes (spec 4.8.1, 4.8.4)."""

    def get(self, request, pk):
        subtopic = get_object_or_404(Subtopic.objects.select_related("concept"), pk=pk)
        blocks = Block.objects.filter(content__subtopic=subtopic)
        if not blocks.exists():
            return Response(
                {"detail": "Este subtema ainda não tem conteúdo."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                "subtopic": subtopic.name,
                "concept": subtopic.concept.name,
                "blocks": BlockSerializer(blocks, many=True).data,
                "resume_block_order": resume_block_order(subtopic),
            }
        )
