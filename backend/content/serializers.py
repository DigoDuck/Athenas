import base64
import binascii

from rest_framework import serializers

from .models import Block, Content, Flashcard


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = ["id", "order", "kind", "heading", "body", "read_at"]


class ContentSerializer(serializers.ModelSerializer):
    blocks = BlockSerializer(many=True, read_only=True)

    class Meta:
        model = Content
        fields = ["raw_markdown", "state", "generated_by", "updated_at", "blocks"]


class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = ["id", "origin", "subtopic", "concept", "label", "front", "back", "state"]


class ImageUploadSerializer(serializers.Serializer):
    """JSON with the bytes in base64, so scripts/theme.py needs no multipart (D-033)."""

    data = serializers.CharField()
    generated_by = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    source_url = serializers.URLField(max_length=500, required=False, allow_blank=True, default="")
    author = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    license = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")

    def validate_data(self, value):
        try:
            return base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError) as error:
            raise serializers.ValidationError("data não é base64 válido") from error

    def validate_generated_by(self, value):
        return value.lower()


class ManualCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = ["subtopic", "concept", "front", "back"]


class MarkdownSerializer(serializers.Serializer):
    markdown = serializers.CharField(trim_whitespace=False)
