from copy import copy

import requests
from httpx import Client


class AssociadoHinovaEndpoints:
    def __init__(self, client: Client) -> None:
        self.base_client = client
        self.client = copy(client)
        self.client.base_url = f"{self.client.base_url}associado/"

    def __buscar(self, cpf_or_codigo: str, search_by: str) -> requests.Response:
        if search_by == "cpf":
            url = f"buscar/{cpf_or_codigo}/cpf"
            return self.client.get(url)
        if search_by == "codigo":
            url = f"buscar/{cpf_or_codigo}/codigo"
            return self.client.get(url)
        raise Exception('Not a valid search_by. Options are "cpf" or "codigo"')

    def buscar_cpf(self, cpf: str):
        resonpes = self.__buscar(cpf, "cpf")
        return resonpes.json(), resonpes.status_code

    def buscar_codigo(self, codigo):
        response = self.__buscar(codigo, "codigo")
        return response.json(), response.status_code

    def list_situation_motivos(self):
        url = "listar/situacaomotivo/todos"
        response = self.base_client.get(url, timeout=30)
        print(response)
        return response
