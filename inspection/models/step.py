import uuid

from django.db import models
from shared_auth.mixins import TimestampedMixin


def step_photo_upload_to(instance, filename):
    ext = filename.split(".")[-1]
    hash_id = uuid.uuid4()
    return f"inspections/{instance.inspection.hash}/steps/{hash_id}.{ext}"


class InspectionStep(TimestampedMixin):
    inspection = models.ForeignKey(
        "inspection.Inspection",
        on_delete=models.CASCADE,
        related_name="steps",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    instructions = models.TextField(
        null=True,
        blank=True,
        help_text="Instruções para o vistoriador realizar este passo.",
    )
    order = models.PositiveIntegerField(default=0)
    photo = models.ImageField(upload_to=step_photo_upload_to, null=True, blank=True)

    class Meta:
        verbose_name = "Passo de Vistoria"
        verbose_name_plural = "Passos de Vistoria"
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.inspection.title} - Passo {self.order}: {self.title}"
