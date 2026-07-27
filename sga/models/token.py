from django.db import models
from shared_auth.mixins import OrganizationMixin, TimestampedMixin


class HinovaToken(OrganizationMixin, TimestampedMixin):
    usuario = models.CharField(max_length=32)
    senha = models.CharField(max_length=32)
    has_activator = models.BooleanField(default=False)

    api_ativador = models.CharField(max_length=128, null=True, blank=True)

    api_token = models.CharField(max_length=192, null=True, blank=True)
    token_usuario = models.CharField(max_length=288, null=True, blank=True)
    token_painel = models.CharField(max_length=128, null=True, blank=True)

    last_sync_terms = models.DateTimeField(null=True, blank=True)
    last_sync_situation_motivo = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Token Hinova"
        verbose_name_plural = "Tokens Hinova"

    def __str__(self):
        return self.usuario

    def get_token(self):
        if self.token_usuario:
            return self.token_usuario

        raise Exception("Token not found")
