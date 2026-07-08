from django.db import models
from shared_auth.mixins import OrganizationUserMixin, TimestampedMixin

from core.mixins.soft_delete import SoftDeleteModelMixin


class InspectionType(
    SoftDeleteModelMixin, OrganizationUserMixin, TimestampedMixin
):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    expiration_days = models.PositiveIntegerField(null=True, blank=True)
    expiration_hours = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Tipo de Vistoria"
        verbose_name_plural = "Tipos de Vistoria"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
