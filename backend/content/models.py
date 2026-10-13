from django.db import models
from django.utils import timezone
from organization.models import Subtopic


class Content(models.Model):
    """The subtopic's Markdown as pasted, always kept (spec 3.2), and its state (spec 4.2.2)."""

    class State(models.TextChoices):
        DRAFT = "draft", "rascunho"
        READY = "ready", "pronto"

    subtopic = models.OneToOneField(Subtopic, on_delete=models.PROTECT, related_name="content")
    raw_markdown = models.TextField()
    state = models.CharField(max_length=5, choices=State, default=State.DRAFT)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subtopic_id} {self.state}"


class Block(models.Model):
    """One `##` section. Rebuilt on every import; blocks have no identity of their own (4.2.6)."""

    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name="blocks")
    order = models.PositiveIntegerField()
    kind = models.CharField(max_length=30)
    heading = models.TextField(blank=True)
    body = models.TextField(blank=True)
    # Carried over on re-import by identical text, never by heading (DECISIONS.md D-015).
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["content_id", "order"]

    def __str__(self):
        return f"{self.order} {self.kind}"


class PracticeQuestion(models.Model):
    """Identity is the label (`P1`...) inside a subtopic (spec 3.3, item 2, and `[C2]`)."""

    subtopic = models.ForeignKey(Subtopic, on_delete=models.PROTECT, related_name="questions")
    label = models.CharField(max_length=10)
    prompt = models.TextField()
    reference_answer = models.TextField(blank=True)
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["subtopic_id", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["subtopic", "label"], name="question_label_unique_per_subtopic"
            ),
        ]

    def __str__(self):
        return self.label


class Attempt(models.Model):
    """Never edited or deleted by the app (spec 3.2)."""

    class Kind(models.TextChoices):
        QUESTION = "question", "pergunta"
        EXPLANATION = "explanation", "explicação"

    class SelfAssessment(models.TextChoices):
        RIGHT = "right", "acertei"
        PARTIAL = "partial", "parcial"
        WRONG = "wrong", "errei"

    subtopic = models.ForeignKey(Subtopic, on_delete=models.PROTECT, related_name="attempts")
    kind = models.CharField(max_length=12, choices=Kind)
    question = models.ForeignKey(
        PracticeQuestion, null=True, blank=True, on_delete=models.PROTECT, related_name="attempts"
    )
    text = models.TextField()
    self_assessment = models.CharField(max_length=7, choices=SelfAssessment)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.kind} {self.self_assessment}"


class Flashcard(models.Model):
    """Cards declared in the Markdown. Identity is the label (`C1`...) inside a subtopic."""

    class State(models.TextChoices):
        PENDING = "pending", "pendente"
        ACTIVE = "active", "ativo"
        SUSPENDED = "suspended", "suspenso"
        REJECTED = "rejected", "rejeitado"

    subtopic = models.ForeignKey(Subtopic, on_delete=models.PROTECT, related_name="flashcards")
    label = models.CharField(max_length=10)
    front = models.TextField()
    back = models.TextField()
    state = models.CharField(max_length=9, choices=State, default=State.PENDING)
    # Where the card goes back to when its label returns to the Markdown (spec 4.2.6, Q8).
    state_before_suspension = models.CharField(max_length=9, blank=True, default="")

    class Meta:
        ordering = ["subtopic_id", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["subtopic", "label"], name="card_label_unique_per_subtopic"
            ),
        ]

    def __str__(self):
        return self.label


class ReviewLog(models.Model):
    """One rating of one card. Rating or editing a card never erases these (spec 3.3, item 5)."""

    class Rating(models.TextChoices):
        AGAIN = "again", "errei"
        HARD = "hard", "parcial"
        GOOD = "good", "acertei"

    flashcard = models.ForeignKey(Flashcard, on_delete=models.PROTECT, related_name="reviews")
    rating = models.CharField(max_length=5, choices=Rating)
    reviewed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["reviewed_at", "id"]

    def __str__(self):
        return f"{self.flashcard_id} {self.rating}"
