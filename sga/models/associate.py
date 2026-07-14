from django.db import models
from shared_auth.mixins import OrganizationMixin, TimestampedMixin

from message.models.contact import Contact


class Associate(OrganizationMixin, TimestampedMixin):
    contact = models.OneToOneField(
        Contact, on_delete=models.CASCADE, related_name="associate"
    )

    codigo_beneficiario = models.CharField(max_length=10, blank=True, null=True)
    codigo_associado = models.CharField(max_length=10)

    class Meta:
        verbose_name = "Associado"
        verbose_name_plural = "Associados"
        unique_together = [
            ("organization_id", "codigo_associado"),
            ("organization_id", "codigo_beneficiario"),
            ("organization_id", "contact"),
        ]
