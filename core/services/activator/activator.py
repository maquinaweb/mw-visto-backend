import httpx
from django.conf import settings

from core.services.activator.activator_sub.vehicle import (
    VehicleActivatorEndpoints,
)
from sga.models.token import HinovaToken


class ActivatorEndPoints:
    def __init__(self, organization_id: int = None):
        if organization_id:
            token = HinovaToken.objects.get(organization_id=organization_id)
            self.base_url = token.api_ativador or settings.ACTIVATOR_URL
        else:
            self.base_url = settings.ACTIVATOR_URL
        self.client = httpx.Client(base_url=self.base_url)

        self.vehicle = VehicleActivatorEndpoints(self.client)
