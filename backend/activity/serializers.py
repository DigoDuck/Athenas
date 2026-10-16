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
