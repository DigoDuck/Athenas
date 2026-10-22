from django.db import transaction
from django.db.models import Max
from rest_framework import serializers

from . import services
from .models import Area, Concept, Settings, Step, Subtopic, Track


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["id", "name"]


class ConceptSerializer(serializers.ModelSerializer):
    study_status = serializers.SerializerMethodField()

    class Meta:
        model = Concept
        fields = ["id", "area", "name", "objective", "study_status"]

    def get_study_status(self, concept):
        return services.concept_status(concept)


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
        # Only the rules of spec 4.4 change it (DECISIONS.md D-024).
        read_only_fields = ["order", "study_status"]

    def create(self, validated_data):
        # Appended after the existing subtopics of the concept.
        with transaction.atomic():
            # Lock the concept row so two inserts cannot take the same position.
            Concept.objects.select_for_update().get(pk=validated_data["concept"].pk)
            siblings = Subtopic.objects.filter(concept=validated_data["concept"])
            last = siblings.aggregate(last=Max("order"))["last"]
            validated_data["order"] = 0 if last is None else last + 1
            return super().create(validated_data)


class SubtopicDetailSerializer(SubtopicSerializer):
    """Adds the suggestion, which costs a few queries, to one subtopic at a time."""

    completion_suggested = serializers.SerializerMethodField()

    class Meta(SubtopicSerializer.Meta):
        fields = [*SubtopicSerializer.Meta.fields, "completion_suggested"]

    def get_completion_suggested(self, subtopic):
        return services.completion_suggested(subtopic)


class StepSerializer(serializers.ModelSerializer):
    concept_name = serializers.CharField(source="concept.name", read_only=True)
    area_name = serializers.CharField(source="concept.area.name", read_only=True)
    concept_status = serializers.SerializerMethodField()

    class Meta:
        model = Step
        fields = ["id", "track", "concept", "concept_name", "area_name", "concept_status", "order"]
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

    def get_concept_status(self, step):
        return services.concept_status(step.concept)


class TrackSerializer(serializers.ModelSerializer):
    steps = StepSerializer(many=True, read_only=True)
    next_step = serializers.SerializerMethodField()

    class Meta:
        model = Track
        fields = ["id", "name", "steps", "next_step"]

    def get_next_step(self, track):
        step = services.next_step(track)
        return step.pk if step else None


def _bounds(low, high, message=None):
    # Our own message: DRF's pt-BR one reads "Certifque-se".
    message = message or f"Use um valor entre {low} e {high}."
    return {
        "min_value": low,
        "max_value": high,
        "error_messages": {"min_value": message, "max_value": message},
    }


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = [
            "review_cap",
            "new_card_cap",
            "desired_retention",
            "pomodoro_focus_minutes",
            "pomodoro_break_minutes",
        ]
        # Bounds a typo cannot cross (DECISIONS.md D-037); the model keeps the wider ones.
        extra_kwargs = {
            "review_cap": _bounds(1, 200),
            "new_card_cap": _bounds(0, 200),
            # The screen shows a percentage; "%%" because Django interpolates the message.
            "desired_retention": _bounds(0.7, 0.97, "Use um valor entre 70%% e 97%%."),
            "pomodoro_focus_minutes": _bounds(1, 180),
            "pomodoro_break_minutes": _bounds(1, 60),
        }

    def validate(self, attrs):
        # New cards take their slots inside the review cap (D-022), so a larger number does nothing.
        review_cap = attrs.get("review_cap", self.instance.review_cap)
        new_card_cap = attrs.get("new_card_cap", self.instance.new_card_cap)
        if new_card_cap > review_cap:
            raise serializers.ValidationError(
                {"new_card_cap": "Use até o limite de revisões por dia, que já inclui os novos."}
            )
        return attrs
