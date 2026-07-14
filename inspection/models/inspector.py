from django.db import models
from shared_auth.mixins import OrganizationUserMixin, TimestampedMixin


class Inspector(OrganizationUserMixin, TimestampedMixin):
    inspection = models.OneToOneField(
        "inspection.Inspection",
        on_delete=models.CASCADE,
        related_name="inspector",
    )
    contact = models.ForeignKey(
        "message.Contact",
        on_delete=models.CASCADE,
        related_name="inspectors",
    )

    class Meta:
        verbose_name = "Inspetor"
        verbose_name_plural = "Inspetores"
