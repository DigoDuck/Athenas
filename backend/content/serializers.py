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
        fields = ["raw_markdown", "state", "updated_at", "blocks"]


class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = ["id", "subtopic", "label", "front", "back", "state"]


class MarkdownSerializer(serializers.Serializer):
    markdown = serializers.CharField(trim_whitespace=False)
