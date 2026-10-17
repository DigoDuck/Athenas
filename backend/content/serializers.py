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


class ManualCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = ["subtopic", "concept", "front", "back"]


class MarkdownSerializer(serializers.Serializer):
    markdown = serializers.CharField(trim_whitespace=False)
