from content.models import Block, PracticeQuestion
from django.shortcuts import get_object_or_404
from organization.models import Subtopic
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SessionEvent
from .serializers import (
    AttemptSerializer,
    PracticeQuestionSerializer,
    ReadingBlockSerializer,
    SessionEventSerializer,
)
from .services import complete_activity, record_attempt, resume_block_order, start_activity


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
        # No content yet is an empty list, so 404 means only that the subtopic does not exist.
        blocks = Block.objects.filter(content__subtopic=subtopic)
        return Response(
            {
                "subtopic": subtopic.name,
                "concept": subtopic.concept.name,
                "blocks": ReadingBlockSerializer(blocks, many=True).data,
                "resume_block_order": resume_block_order(subtopic),
            }
        )


class PracticeView(APIView):
    """Questions with a reference answer and every attempt, newest first (spec 4.8.3)."""

    def get(self, request, pk):
        subtopic = get_object_or_404(Subtopic.objects.select_related("concept"), pk=pk)
        questions = PracticeQuestion.objects.filter(subtopic=subtopic, archived=False).exclude(
            reference_answer=""
        )
        attempts = subtopic.attempts.order_by("-created_at", "-id")
        return Response(
            {
                "subtopic": subtopic.name,
                "concept": subtopic.concept.name,
                "questions": PracticeQuestionSerializer(questions, many=True).data,
                "attempts": AttemptSerializer(attempts, many=True).data,
            }
        )


class AttemptView(APIView):
    """Create-only: attempts are never edited or deleted (spec 3.2)."""

    def post(self, request):
        serializer = AttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            attempt = record_attempt(**serializer.validated_data)
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_409_CONFLICT)
        return Response(AttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)
