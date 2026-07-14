from django.db import models
from shared_auth.mixins import OrganizationMixin, TimestampedMixin


class Contact(OrganizationMixin, TimestampedMixin):
    document = models.CharField(
        max_length=14, db_index=True, blank=True, null=True
    )
    name = models.CharField(max_length=200, blank=True, null=True)
    email = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    saved = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Contato"
        verbose_name_plural = "Contatos"
        unique_together = ("organization_id", "email", "document")
