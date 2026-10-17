from dataclasses import asdict

from content.models import Attempt, Block, Image, PracticeQuestion, ReviewLog
from content.parser import IMAGE_RE, split_segments, without_reference_answers
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


class ReviewSerializer(serializers.ModelSerializer):
    event = serializers.PrimaryKeyRelatedField(queryset=SessionEvent.objects.all(), write_only=True)

    class Meta:
        model = ReviewLog
        fields = ["id", "event", "flashcard", "rating", "reviewed_at"]
        read_only_fields = ["reviewed_at"]


class PracticeQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeQuestion
        fields = ["id", "label", "prompt", "reference_answer"]


class ReadingBlockSerializer(serializers.ModelSerializer):
    """A block for reading: its body cut into text, code, `[!ia]` callouts and images, never raw."""

    segments = serializers.SerializerMethodField()

    class Meta:
        model = Block
        fields = ["order", "kind", "heading", "read_at", "segments"]

    def get_segments(self, block):
        body = block.body
        if block.kind == "Prática":
            body = without_reference_answers(body)
        segments = [asdict(segment) for segment in split_segments(body)]
        names = [s["image"] for s in segments if s["kind"] == "image"]
        found = {i.name: i for i in Image.objects.filter(name__in=names).defer("data")}
        for segment in segments:
            if segment["kind"] == "image":
                segment["image"] = _figure(segment, found.get(segment["image"]))
        return segments


def _figure(segment, image):
    """What the screen shows under a picture; `url` is None when it was never uploaded (D-033)."""
    alt, _, title = IMAGE_RE.match(segment["text"]).groups(default="")
    credit = ("generated_by", "source_url", "author", "license")
    return {
        "name": segment["image"],
        "caption": title or alt,
        "url": image and f"/api/images/{image.name}/",
        **{key: getattr(image, key, "") for key in credit},
    }
