
from .termo import TermoHinovaEndpoints
from .termo_fallback import TermoHinovaFallbackEndpoints
from .veiculo import VeiculoHinovaEndpoints


class TermoHinovaResilienteEndpoints(TermoHinovaEndpoints):
    def __init__(
        self,
        client,
        panel_token: str,
        timeout_seconds: int = 15
    ) -> None:
        super().__init__(client)
        self.veiculo = VeiculoHinovaEndpoints(client)
        self.painel = TermoHinovaFallbackEndpoints(
            panel_token=panel_token,
            request_timeout=timeout_seconds,
        )

    def emitir(self, body):
        api_error = None

        # try:
        #     response = super().emitir(body)
        #     if response.status_code < 400:
        #         return response
        #     api_error = response
        # except (httpx.TimeoutException, httpx.HTTPError):
        #     pass

        painel_response = self.painel.emitir(dict(body or {}))
        if painel_response.status_code < 400:
            return painel_response
        return api_error or painel_response
