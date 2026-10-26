import base64
import binascii
import re

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


OPTIONAL = {"required": False, "allow_blank": True, "default": ""}


class ImageUploadSerializer(serializers.Serializer):
    """JSON with the bytes in base64, so scripts/theme.py needs no multipart (D-033)."""

    data = serializers.CharField()
    generated_by = serializers.CharField(max_length=30, **OPTIONAL)
    source_url = serializers.URLField(max_length=500, **OPTIONAL)
    author = serializers.CharField(max_length=200, **OPTIONAL)
    license = serializers.CharField(max_length=100, **OPTIONAL)

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


class ThemeSerializer(serializers.Serializer):
    """The "Novo tema" paste: where it goes, which AI wrote it, and its answer (D-040)."""

    area = serializers.CharField(max_length=120)
    track = serializers.CharField(max_length=120)
    origem = serializers.CharField(max_length=60)
    markdown = serializers.CharField(trim_whitespace=False)

    def validate_origem(self, value):
        # Written into each frontmatter line, so one word: no line break can sneak a key in.
        value = re.sub(r"[\s_]+", "-", value.lower())
        if not re.fullmatch(r"[\w.-]{1,30}", value):
            raise serializers.ValidationError(
                "IA usada: até 30 letras, números, ponto ou hífen, como gemini ou chatgpt."
            )
        return value
