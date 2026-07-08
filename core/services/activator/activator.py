import httpx
from django.conf import settings

from core.services.activator.activator_sub.vehicle import (
    VehicleActivatorEndpoints,
)


class ActivatorEndPoints:
    base_url = settings.ACTIVATOR_URL
    client = httpx.Client(base_url=base_url)

    vehicle = VehicleActivatorEndpoints(client)
