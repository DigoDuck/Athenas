from content.models import Attempt, PracticeQuestion
from rest_framework import serializers

from .models import SessionEvent


class SessionEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionEvent
        fields = [
            "id",
            "kind",
            "subtopic",
            "block_order",
            "question",
            "started_at",
            "ended_at",
            "completed_at",
        ]
        read_only_fields = ["started_at", "ended_at", "completed_at"]


class AttemptSerializer(serializers.ModelSerializer):
    # The event names the subject; kind, subtopic and question are copied from it.
    event = serializers.PrimaryKeyRelatedField(queryset=SessionEvent.objects.all(), write_only=True)

    class Meta:
        model = Attempt
        fields = ["id", "event", "kind", "question", "text", "self_assessment", "created_at"]
        read_only_fields = ["kind", "question", "created_at"]


class PracticeQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeQuestion
        fields = ["id", "label", "prompt", "reference_answer"]
