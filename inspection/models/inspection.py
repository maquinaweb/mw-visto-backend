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
    notify_email = models.BooleanField(default=False)
    notify_whatsapp = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Vistoria"
        verbose_name_plural = "Vistorias"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            try:
                old_status = Inspection.objects.get(pk=self.pk).status
            except Inspection.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        if (
            self.status == self.Status.REJECTED
            and old_status != self.Status.REJECTED
        ):
            # Check if there are any rejected steps
            has_rejected_steps = self.steps.filter(status="rejected").exists()
            if not has_rejected_steps:
                # No steps were explicitly rejected -> reject the entire inspection (set all steps to "rejected")
                self.steps.all().update(status="rejected")

