from django.db import transaction
from django.db.models import Max
from rest_framework import serializers

from .models import Area, Concept, Settings, Step, Subtopic, Track


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["id", "name"]


class ConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concept
        fields = ["id", "area", "name", "objective"]


class SubtopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtopic
        fields = [
            "id",
            "concept",
            "name",
            "order",
            "level",
            "perceived_difficulty",
            "study_status",
            "review_needed",
        ]
        read_only_fields = ["order"]

    def create(self, validated_data):
        # Appended after the existing subtopics of the concept.
        with transaction.atomic():
            # Lock the concept row so two inserts cannot take the same position.
            Concept.objects.select_for_update().get(pk=validated_data["concept"].pk)
            siblings = Subtopic.objects.filter(concept=validated_data["concept"])
            last = siblings.aggregate(last=Max("order"))["last"]
            validated_data["order"] = 0 if last is None else last + 1
            return super().create(validated_data)


class StepSerializer(serializers.ModelSerializer):
    concept_name = serializers.CharField(source="concept.name", read_only=True)
    area_name = serializers.CharField(source="concept.area.name", read_only=True)

    class Meta:
        model = Step
        fields = ["id", "track", "concept", "concept_name", "area_name", "order"]
        read_only_fields = ["order"]
        # The unique (track, concept) constraint is reported as a field error by default.
        validators = []

    def validate(self, attrs):
        if Step.objects.filter(track=attrs["track"], concept=attrs["concept"]).exists():
            raise serializers.ValidationError("Este conceito já está na trilha.")
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            # Lock the track row so two inserts cannot take the same position.
            Track.objects.select_for_update().get(pk=validated_data["track"].pk)
            last = Step.objects.filter(track=validated_data["track"]).aggregate(last=Max("order"))
            validated_data["order"] = 0 if last["last"] is None else last["last"] + 1
            return super().create(validated_data)


class TrackSerializer(serializers.ModelSerializer):
    steps = StepSerializer(many=True, read_only=True)

    class Meta:
        model = Track
        fields = ["id", "name", "steps"]


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = [
            "review_cap",
            "new_card_cap",
            "desired_retention",
            "pomodoro_focus_minutes",
            "pomodoro_break_minutes",
            "backup_folder",
        ]
