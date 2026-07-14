from django.db import models
from shared_auth.mixins import OrganizationMixin, TimestampedMixin


class VehicleSGA(OrganizationMixin, TimestampedMixin):
    inspection = models.OneToOneField(
        "inspection.Inspection",
        on_delete=models.CASCADE,
        related_name="vehicle_sga",
    )

    plate = models.CharField(max_length=17, null=True, blank=True)
    chassi = models.CharField(max_length=17, null=True, blank=True)
    codigo_veiculo = models.CharField(max_length=10, null=True, blank=True)
    codigo_evento = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        verbose_name = "Veículo SGA"
        verbose_name_plural = "Veículos SGA"
