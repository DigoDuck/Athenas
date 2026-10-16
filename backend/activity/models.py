from content.models import PracticeQuestion
from django.db import models
from django.utils import timezone
from organization.models import Subtopic


class SessionEvent(models.Model):
    """One row per activity (spec 3.2). Create-only, except completing it once (D-020)."""

    class Kind(models.TextChoices):
        READING = "reading", "leitura"
        NOTEBOOK = "notebook", "caderno"
        QUESTION = "question", "pergunta"
        EXPLANATION = "explanation", "explicação"
        REVIEW_SESSION = "review_session", "sessão de revisão"
        APP_OPENED = "app_opened", "app aberto"

    kind = models.CharField(max_length=14, choices=Kind)
    # The subject, never a block: blocks are rebuilt on every re-import (DECISIONS.md D-017).
    subtopic = models.ForeignKey(
        Subtopic, null=True, blank=True, on_delete=models.PROTECT, related_name="events"
    )
    block_order = models.PositiveIntegerField(null=True, blank=True)
    question = models.ForeignKey(
        PracticeQuestion, null=True, blank=True, on_delete=models.PROTECT, related_name="events"
    )
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    # Stays empty when the activity is abandoned; only completed events make a session (Q1).
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["started_at", "id"]

    def __str__(self):
        return f"{self.kind} {self.started_at:%Y-%m-%d %H:%M}"
