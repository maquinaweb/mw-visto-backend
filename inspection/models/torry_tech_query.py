from django.db import models
from shared_auth.mixins import OrganizationMixin, TimestampedMixin
from core.mixins.soft_delete import SoftDeleteModelMixin


class TorryTechQuery(SoftDeleteModelMixin, OrganizationMixin, TimestampedMixin):
    inspection = models.ForeignKey(
        "inspection.Inspection",
        on_delete=models.CASCADE,
        related_name="torry_tech_queries",
        null=True,
        blank=True,
    )
    plate = models.CharField(
        max_length=20, db_index=True, null=True, blank=True
    )
    chassi = models.CharField(
        max_length=30, db_index=True, null=True, blank=True
    )
    cons = models.CharField(max_length=10, default="83")  # e.g., "78" or "83"
    uf = models.CharField(max_length=10, null=True, blank=True)
    id_pesquisa = models.CharField(max_length=50, null=True, blank=True)
    status_consulta = models.CharField(max_length=50, null=True, blank=True)
    success = models.BooleanField(default=False)
    message = models.TextField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)
    link_impressao = models.URLField(max_length=500, null=True, blank=True)

    class Meta:
        verbose_name = "Consulta Torry Tech"
        verbose_name_plural = "Consultas Torry Tech"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Consulta {self.cons} - {self.plate or self.chassi} ({self.status_consulta})"
