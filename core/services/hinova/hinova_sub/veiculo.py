from copy import copy

import requests
from httpx import Client


class VeiculoHinovaEndpoints:
    def __init__(self, client: Client) -> None:
        self.base_client = client
        self.client = copy(client)
        self.client.base_url = f"{self.client.base_url}veiculo/"

    def change_situation(
        self,
        codigo_veiculo: str,
        codigo_situacao: str,
        codigo_motivo: str = None,
        observacao: str = None,
    ):
        url = "alterar-situacao-para/"
        response = self.client.post(
            url,
            json={
                "codigo_situacao": codigo_situacao,
                "codigo_veiculo": codigo_veiculo,
                "codigo_situacaomotivo": codigo_motivo,
                "observacao": observacao,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response

    def buscar(self, placa) -> requests.Response:
        url = f"buscar/{placa}"
        response = self.client.get(url)
        return response

    def buscar_chassi(self, chassi) -> requests.Response:
        url = f"buscar/{chassi}/chassi"
        response = self.client.get(url)
        return response

    def buscar_by_code(self, code) -> requests.Response:
        url = f"buscar/{code}/codigo"
        response = self.client.get(url)
        return response

    def listar_tipo_veiculo(self):
        url = "listar/tipo-veiculo/todos"
        response = self.client.get(url)
        return response

    def listar_eventos(self, placa):
        url = f"listar/evento-veiculo/{placa}"
        response = self.base_client.get(url)
        return response

    def anexo(self, body):
        url = "foto/cadastrar"
        response = self.client.post(url, json=body, timeout=25)
        return response

    # def anexo_by_document(self, subscription: Subscription, document: dict):
    #     foto = {
    #         "nome_arquivo": subscription.nome + ".pdf",
    #         "codigo_tipo": "6",
    #         "link": document["signed_file"],
    #     }
    #     return self.anexo(
    #         {
    #             "codigo_veiculo": subscription.codigo_veiculo,
    #             "foto": [foto],
    #         }
    #     )

    def list_situations(self):
        url = "listar/situacao/todos"
        response = self.client.get(url)
        return response
