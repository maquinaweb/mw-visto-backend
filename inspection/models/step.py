import uuid

from django.db import models
from shared_auth.mixins import TimestampedMixin


def step_file_upload_to(instance, filename):
    ext = filename.split(".")[-1]
    hash_id = uuid.uuid4()
    return f"inspections/{instance.inspection.hash}/steps/{hash_id}.{ext}"


# Alias for backward compatibility with old migrations
step_photo_upload_to = step_file_upload_to


class InspectionStep(TimestampedMixin):
    inspection = models.ForeignKey(
        "inspection.Inspection",
        on_delete=models.CASCADE,
        related_name="steps",
    )
    type_step = models.ForeignKey(
        "inspection.InspectionTypeStep",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pendente"),
            ("approved", "Aprovada"),
            ("rejected", "Reprovada"),
        ],
        default="pending",
    )
    order = models.PositiveIntegerField(default=0)
    file = models.FileField(
        upload_to=step_file_upload_to, null=True, blank=True
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Passo de Vistoria"
        verbose_name_plural = "Passos de Vistoria"
        ordering = ["order", "created_at"]

    def __str__(self):
        step_title = self.type_step.title if self.type_step else "Passo"
        return f"{self.inspection.title} - Passo {self.order}: {step_title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            try:
                old_status = InspectionStep.objects.get(pk=self.pk).status
            except InspectionStep.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        if (
            self.status == "rejected"
            and old_status != "rejected"
            and self.type_step
            and self.type_step.is_sequential
        ):
            steps = list(self.inspection.steps.all().order_by("order"))
            try:
                current_idx = steps.index(self)
            except ValueError:
                current_idx = -1
                for idx, step in enumerate(steps):
                    if step.id == self.id:
                        current_idx = idx
                        break

            if current_idx != -1:
                to_reject = set()

                # Traverse backwards
                for i in range(current_idx - 1, -1, -1):
                    step = steps[i]
                    if step.type_step and step.type_step.is_sequential:
                        to_reject.add(step.id)
                    else:
                        break

                # Traverse forwards
                for i in range(current_idx + 1, len(steps)):
                    step = steps[i]
                    if step.type_step and step.type_step.is_sequential:
                        to_reject.add(step.id)
                    else:
                        break

                if to_reject:
                    InspectionStep.objects.filter(id__in=to_reject).update(
                        status="rejected"
                    )
