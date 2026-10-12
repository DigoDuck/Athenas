from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Area(models.Model):
    name = models.CharField("nome", max_length=120, unique=True)

    class Meta:
        verbose_name = "área"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Concept(models.Model):
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name="concepts")
    name = models.CharField(max_length=160)
    objective = models.TextField(blank=True)

    class Meta:
        ordering = ["area__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["area", "name"],
                name="concept_name_unique_per_area",
                violation_error_message="Já existe um conceito com este nome nesta área.",
            ),
        ]

    def __str__(self):
        return self.name


class Subtopic(models.Model):
    class Level(models.TextChoices):
        UNSET = "", "não definido"
        BEGINNER = "iniciante", "iniciante"
        INTERMEDIATE = "intermediario", "intermediário"
        ADVANCED = "avancado", "avançado"
        EXPERT = "especialista", "especialista"

    class Difficulty(models.TextChoices):
        UNSET = "unset", "não definida"
        EASY = "easy", "fácil"
        HARD = "hard", "difícil"

    class StudyStatus(models.TextChoices):
        NOT_STARTED = "not_started", "não iniciado"
        IN_PROGRESS = "in_progress", "em andamento"
        COMPLETED = "completed", "concluído"

    concept = models.ForeignKey(Concept, on_delete=models.PROTECT, related_name="subtopics")
    name = models.CharField(max_length=160)
    order = models.PositiveIntegerField(default=0)
    # The four classification fields are independent of each other (spec 3.2).
    level = models.CharField(max_length=20, choices=Level, blank=True, default=Level.UNSET)
    perceived_difficulty = models.CharField(
        max_length=10, choices=Difficulty, default=Difficulty.UNSET
    )
    study_status = models.CharField(
        max_length=12, choices=StudyStatus, default=StudyStatus.NOT_STARTED
    )
    review_needed = models.BooleanField(default=False)

    class Meta:
        ordering = ["concept_id", "order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["concept", "name"],
                name="subtopic_name_unique_per_concept",
                violation_error_message="Já existe um subtema com este nome neste conceito.",
            ),
        ]

    def __str__(self):
        return self.name


class Track(models.Model):
    name = models.CharField("nome", max_length=120, unique=True)

    class Meta:
        verbose_name = "trilha"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Step(models.Model):
    """One concept's position in a track. A concept appears once per track."""

    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="steps")
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name="steps")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["track_id", "order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["track", "concept"], name="step_concept_once_per_track"
            ),
        ]

    def __str__(self):
        return f"{self.track_id}:{self.order}:{self.concept_id}"


class Settings(models.Model):
    """Single row (pk=1). Read it through `Settings.load()`."""

    review_cap = models.PositiveIntegerField(default=20)
    new_card_cap = models.PositiveIntegerField(default=5)
    desired_retention = models.FloatField(
        default=0.9, validators=[MinValueValidator(0.01), MaxValueValidator(0.99)]
    )
    pomodoro_focus_minutes = models.PositiveIntegerField(
        default=25, validators=[MinValueValidator(1), MaxValueValidator(180)]
    )
    pomodoro_break_minutes = models.PositiveIntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(60)]
    )
    backup_folder = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name_plural = "settings"

    def __str__(self):
        return "Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
