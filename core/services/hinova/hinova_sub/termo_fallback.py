import re
from html import unescape
from urllib.parse import quote

import httpx
from httpx import Response


class TermoHinovaFallbackEndpoints:
    base_url = "https://saturno.hinova.com.br/sga/sgav4_clube_autos/v5"
    pdf_lambda_url = "http://186.202.57.39:3001/"

    def __init__(
        self,
        panel_token: str,
        request_timeout: int = 15,
    ) -> None:
        self.panel_token = panel_token
        self.request_timeout = request_timeout

    def emitir(self, body: dict) -> Response:
        codigo_termo = self._as_text(body.get("codigo_termo"))
        plate = self._as_text(body.get("placa"))

        if not codigo_termo:
            return Response(
                status_code=400,
                json={
                    "error": "Fallback do painel requer codigo_termo.",
                },
            )

        if not plate:
            return Response(
                status_code=400,
                json={
                    "error": (
                        "Fallback do painel requer placa ou ids do painel "
                        "(codigo_associado/codigo_veiculo)."
                    ),
                },
            )

        veiculo = self._buscar_veiculo_por_placa(plate)
        if not veiculo:
            return Response(
                status_code=404,
                json={
                    "error": "Veiculo nao encontrado no painel da Hinova para a placa informada.",
                },
            )
        codigo_associado = self._as_text(veiculo.get("id_associado"))
        codigo_veiculo = self._as_text(veiculo.get("id"))

        if not codigo_associado or not codigo_veiculo:
            return Response(
                status_code=400,
                json={
                    "error": (
                        "Fallback do painel requer placa valida ou ids do painel "
                        "(codigo_associado/codigo_veiculo)."
                    ),
                },
            )

        response = self._listar_termos_painel(codigo_associado, codigo_veiculo)
        if response.status_code >= 400:
            return Response(
                status_code=response.status_code,
                json={"error": "Falha ao listar termos no painel da Hinova."},
            )

        url_visualizacao = self._buscar_url_termo(response.text, codigo_termo)
        if not url_visualizacao:
            return Response(
                status_code=404,
                json={"error": "Termo nao encontrado no painel da Hinova."},
            )

        return Response(
            status_code=200,
            json={
                "link_pdf": self._montar_pdf_url(url_visualizacao),
                "codigo_emissao": codigo_termo,
                "ferramenta": body.get("ferramenta"),
                "url_visualizacao": url_visualizacao,
                "fallback": True,
            },
        )

    def _listar_termos_painel(
        self,
        codigo_associado: str,
        codigo_veiculo: str,
    ) -> Response:
        url = f"{self.base_url.rstrip('/')}/templates/Termoconfiguracao/actions.php"
        payload = {
            "acao": "lista_termos",
            "id_veiculo": codigo_veiculo,
            "id_associado": codigo_associado,
            "id_objeto": codigo_veiculo,
            "tipo": "V",
            "controle_power": codigo_veiculo,
        }
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.base_url.rstrip('/')}/Termoconfiguracao/listar",
            "Cookie": f"_u3195={self.panel_token}",
        }

        with httpx.Client(
            timeout=self.request_timeout,
            follow_redirects=True,
        ) as client:
            return client.post(url, data=payload, headers=headers)

    def _buscar_url_termo(self, html: str, codigo_termo: str) -> str | None:
        target = self._norm(codigo_termo)

        for row in re.finditer(
            r"<tr[^>]*>([\s\S]*?)</tr>", html, re.IGNORECASE
        ):
            row_html = row.group(1)
            columns = [
                col.group(1)
                for col in re.finditer(
                    r"<td[^>]*>([\s\S]*?)</td>",
                    row_html,
                    re.IGNORECASE,
                )
            ]
            if len(columns) < 2:
                continue

            codigo_linha = self._norm(self._strip_html(columns[0]))
            if codigo_linha != target:
                continue

            href = re.search(
                r'<a[^>]*href="([^"]+)"', columns[1], re.IGNORECASE
            )
            if href:
                return unescape(href.group(1))

            # Fallback: alguns layouts expõem a URL no botão "envio_termo_pdf".
            button_value = re.search(
                r'id="envio_termo_pdf"[^>]*value="([^"]+)"',
                row_html,
                re.IGNORECASE,
            )
            if button_value:
                raw_value = unescape(button_value.group(1))
                return raw_value.split("|", 1)[0].strip()

        return None

    def _buscar_veiculo_por_placa(self, placa: str) -> dict | None:
        url = f"{self.base_url.rstrip('/')}/autocomplete.php"
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.base_url.rstrip('/')}/Termoconfiguracao/listar",
            "Cookie": f"_u3195={self.panel_token}",
        }
        params = {
            "obj": "veiculo_agregado_consulta",
            "coluna": "placa",
            "term": placa,
        }

        with httpx.Client(
            timeout=self.request_timeout,
            follow_redirects=True,
        ) as client:
            response = client.get(url, params=params, headers=headers)

        if response.status_code >= 400:
            return None

        try:
            payload = response.json()
        except ValueError:
            return None

        if not isinstance(payload, list) or not payload:
            return None

        placa_normalizada = self._normalizar_placa(placa)
        encontrado = next(
            (
                item
                for item in payload
                if self._normalizar_placa(self._as_text(item.get("placa")))
                == placa_normalizada
            ),
            payload[0],
        )

        if not self._as_text(encontrado.get("id")) or not self._as_text(
            encontrado.get("id_associado")
        ):
            return None

        return encontrado

    def _montar_pdf_url(self, url_visualizacao: str) -> str:
        base = self.pdf_lambda_url.rstrip("/")
        return f"{base}?hide_class=mensagem-aceite&url={quote(url_visualizacao, safe='')}"

    def _strip_html(self, value: str) -> str:
        return re.sub(
            r"\s+", " ", re.sub(r"<[^>]*>", " ", unescape(value))
        ).strip()

    def _norm(self, value: str) -> str:
        return re.sub(r"[^0-9A-Za-z]", "", str(value or "")).upper()

    def _as_text(self, value) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _normalizar_placa(self, value: str) -> str:
        return re.sub(r"[^A-Za-z0-9]", "", value or "").upper()
