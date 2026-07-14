import uuid

from django.db import models
from shared_auth.mixins import OrganizationUserMixin, TimestampedMixin

from core.mixins.soft_delete import SoftDeleteModelMixin


class Inspection(SoftDeleteModelMixin, OrganizationUserMixin, TimestampedMixin):
    class Status(models.TextChoices):
        EMITTED = "emitted", "Emitida"
        VIEWED = "viewed", "Visualizada"
        PERFORMED = "performed", "Realizada"
        APPROVED = "approved", "Aprovada"
        REJECTED = "rejected", "Reprovada"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.EMITTED,
    )

    inspection_type = models.ForeignKey(
        "inspection.InspectionType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inspections",
    )
    motive = models.ForeignKey(
        "inspection.InspectionMotive",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inspections",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    hash = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    scheduled_to = models.DateTimeField(null=True, blank=True)
    notify_email = models.BooleanField(default=False)
    notify_whatsapp = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Vistoria"
        verbose_name_plural = "Vistorias"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
