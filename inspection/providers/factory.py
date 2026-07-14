from rest_framework.exceptions import ValidationError
from inspection.providers.base import BaseProvider


def get_provider_instance(provider_name: str) -> BaseProvider:
    # Dynamically import provider classes to prevent circular dependencies
    if provider_name == "sga":
        from sga.providers.sga_provider import SGAProvider

        return SGAProvider()

    raise ValidationError(
        f"Provedor '{provider_name}' não suportado ou configurado."
    )
