from django.db import models
from shared_auth.mixins import OrganizationUserMixin, TimestampedMixin

from core.mixins.soft_delete import SoftDeleteModelMixin


class InspectionType(
    SoftDeleteModelMixin, OrganizationUserMixin, TimestampedMixin
):
    class Providers(models.TextChoices):
        SGA = "sga", "SGA"

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    provider = models.CharField(
        max_length=50,
        choices=Providers.choices,
        default=Providers.SGA,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Tipo de Vistoria"
        verbose_name_plural = "Tipos de Vistoria"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
