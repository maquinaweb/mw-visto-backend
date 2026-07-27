from django.db import models
from shared_auth.mixins import OrganizationMixin, TimestampedMixin
from core.mixins.soft_delete import SoftDeleteModelMixin


class AutomationRule(OrganizationMixin, TimestampedMixin, SoftDeleteModelMixin):
    class Provider(models.TextChoices):
        ATIVADOR = "ativador", "Ativador (SGA / Autovisto)"

    class Event(models.TextChoices):
        EMITTED = "emitted", "Vistoria Emitida"
        APPROVED = "approved", "Vistoria Aprovada"
        SIGNATURE_CREATED = "signature_created", "Termo Gerado"
        SIGNATURE_SIGNED = "signature_signed", "Termo Assinado"
        SIGNATURE_APPROVED = "signature_approved", "Assinatura Aprovada"

    name = models.CharField(max_length=255, blank=True, default="")
    provider = models.CharField(
        max_length=50, choices=Provider.choices, default=Provider.ATIVADOR
    )
    is_active = models.BooleanField(default=True)
    event = models.CharField(max_length=50, choices=Event.choices)

    inspection_type = models.ForeignKey(
        "inspection.InspectionType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="automation_rules",
    )
    inspection_motive = models.ForeignKey(
        "inspection.InspectionMotive",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="automation_rules",
    )

    target_situation_code = models.IntegerField(
        help_text="Código da situação no Ativador/SGA"
    )
    target_situation_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Nome da situação no Ativador/SGA",
    )
    observation_template = models.CharField(
        max_length=255, blank=True, default=""
    )

    class Meta:
        verbose_name = "Regra de Automação"
        verbose_name_plural = "Regras de Automação"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.name or not self.name.strip():
            event_label = self.get_event_display()
            sit_label = self.target_situation_name
            self.name = (
                f"{event_label} ➔ {sit_label}" if sit_label else event_label
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_event_display()} -> {self.target_situation_code})"
