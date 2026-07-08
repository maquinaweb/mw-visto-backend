from httpx import Client


class VehicleActivatorEndpoints:
    def __init__(self, client: Client) -> None:
        self.client = client

    def change_situation(
        self,
        codigo_veiculo: str,
        codigo_situacao: int,
        codigo_motivo: str = None,
        observacao: str = None,
    ):
        response = self.client.patch(
            "/vehicle/change/",
            data={
                "situation": codigo_situacao,
                "codigo_veiculo": codigo_veiculo,
                "motivo": codigo_motivo,
                "reason": observacao,
            },
            timeout=120,
        )
        # response.raise_for_status()
        return response
