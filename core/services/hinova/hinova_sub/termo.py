from copy import copy

import requests
from httpx import Client


class TermoHinovaEndpoints:
    def __init__(self, client: Client) -> None:
        self.client = copy(client)
        self.client.base_url = f"{self.client.base_url}termo/"

    def listar(self) -> requests.Response:
        url = "listar"
        response = self.client.get(url)
        return response

    def emitir(self, body) -> requests.Response:
        url = "emitir"
        response = self.client.post(url, json=body)
        return response
