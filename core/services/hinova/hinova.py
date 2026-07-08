import httpx
from django.conf import settings
from httpx import Client, Response

from sga.models.token import HinovaToken

from .hinova_sub.associado import AssociadoHinovaEndpoints
from .hinova_sub.termo_resiliente import TermoHinovaResilienteEndpoints
from .hinova_sub.veiculo import VeiculoHinovaEndpoints


class HinovaEndPoints:
    def __init__(self, organization_id: int):
        hinova_token = HinovaToken.objects.get(organization_id=organization_id)
        api_token = hinova_token.get_token()
        panel_token = hinova_token.token_painel or api_token
        timeout_seconds = getattr(settings, "HINOVA_TIMEOUT_SECONDS", 15)

        self.client = Client(
            base_url=settings.HINOVA_URL,
            headers={
                "authorization": f"Bearer {api_token}",
                "content-type": "application/json",
            },
            timeout=timeout_seconds,
        )

        self.veiculo = VeiculoHinovaEndpoints(self.client)
        self.associado = AssociadoHinovaEndpoints(self.client)
        self.termo = TermoHinovaResilienteEndpoints(
            client=self.client,
            panel_token=panel_token,
            timeout_seconds=timeout_seconds,
        )

    @staticmethod
    def get_token(usuario: str, senha: str, token: str):
        return httpx.post(
            f"{settings.HINOVA_URL}/usuario/autenticar",
            json={
                "usuario": usuario,
                "senha": senha,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

    @staticmethod
    def handle_error(
        response: Response,
        message: str = "Houve um erro ao tentar acessar a HINOVA",
    ):
        try:
            data = response.json()
            error = data.get("error")

            if isinstance(error, list):
                error = error[0]
            error = error or message
        except (ValueError, TypeError):
            error = message
        return error
