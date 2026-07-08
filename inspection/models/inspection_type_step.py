import uuid

from django.db import models
from shared_auth.mixins import TimestampedMixin


def type_step_photo_upload_to(instance, filename):
    ext = filename.split(".")[-1]
    hash_id = uuid.uuid4()
    return (
        f"inspection_types/{instance.inspection_type.id}/steps/{hash_id}.{ext}"
    )


class InspectionTypeStep(TimestampedMixin):
    inspection_type = models.ForeignKey(
        "inspection.InspectionType",
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
    instruction_image = models.ImageField(
        upload_to=type_step_photo_upload_to, null=True, blank=True
    )
    is_sequential = models.BooleanField(default=False)
    allow_attachment = models.BooleanField(default=False)
    high_resolution = models.CharField(
        max_length=10,
        choices=[("high", "Alta"), ("low", "Baixa")],
        default="high",
    )

    class Meta:
        verbose_name = "Passo do Tipo de Vistoria"
        verbose_name_plural = "Passos do Tipo de Vistoria"
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.inspection_type.name} - Passo {self.order}: {self.title}"
