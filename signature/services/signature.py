import logging
import requests
from decouple import config

logger = logging.getLogger(__name__)


class SignatureService:
    def __init__(self, auth_header=None, org_header=None):
        self.base_url = config(
            "SIGN_API_URL", default="http://localhost:8001/api"
        ).rstrip("/")
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if auth_header:
            self.headers["Authorization"] = auth_header
        if org_header:
            self.headers["X-Organization"] = org_header

    def create_term_pdf(
        self,
        term_code,
        associate_code,
        beneficiary_code=None,
        vehicle_code=None,
        event_code=None,
        plate=None,
        tool_name=None,
    ):
        url = f"{self.base_url}/type-terms/"
        payload = {
            "codigo_termo": term_code,
            "codigo_associado": associate_code,
            "ferramenta": tool_name,
        }
        if beneficiary_code:
            payload["codigo_beneficiario"] = beneficiary_code
        if vehicle_code:
            payload["codigo_veiculo"] = vehicle_code
        if event_code:
            payload["codigo_evento"] = event_code
        if plate:
            payload["placa"] = plate

        logger.info(
            f"Calling type-terms on mw-sign-backend: {url} with payload {payload}"
        )
        response = requests.post(
            url, json=payload, headers=self.headers, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def get_term_positions(self, term_id):
        url = f"{self.base_url}/positions/get-last/"
        logger.info(
            f"Calling positions/get-last on mw-sign-backend: {url} for term {term_id}"
        )
        response = requests.get(
            url, params={"type_term": term_id}, headers=self.headers, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def create_protocol(self, payload):
        url = f"{self.base_url}/protocols/"
        logger.info(f"Calling protocols on mw-sign-backend: {url}")
        response = requests.post(
            url, json=payload, headers=self.headers, timeout=30
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"mw-sign-backend error response: {response.text}")
            raise e
        return response.json()

    def update_protocol_positions(self, protocol_id, positions):
        url = f"{self.base_url}/protocols/{protocol_id}/"
        logger.info(f"Calling patch protocol on mw-sign-backend: {url}")
        response = requests.patch(
            url, json={"positions": positions}, headers=self.headers, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def send_signature_notification(self, protocol_id, channel="email"):
        url = f"{self.base_url}/protocols/send-signatures/"
        logger.info(
            f"Calling send-signatures on mw-sign-backend: {url} for protocol {protocol_id}"
        )
        payload = {
            "type": channel,
            "ids": [protocol_id],
        }
        response = requests.post(
            url, json=payload, headers=self.headers, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def get_protocol_by_hash(self, hash):
        url = f"{self.base_url}/protocols/by_hash/"
        logger.info(
            f"Calling protocols/by_hash on mw-sign-backend: {url} for hash {hash}"
        )
        response = requests.get(
            url, params={"hash": hash}, headers=self.headers, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def approve_protocol_signatories(self, protocol_hash):
        protocol_data = self.get_protocol_by_hash(protocol_hash)
        if not protocol_data:
            return
        signatories = protocol_data.get("signatories") or []
        for signatory in signatories:
            sig_id = signatory.get("id")
            if sig_id:
                try:
                    url = f"{self.base_url}/signatories/{sig_id}/approve/"
                    response = requests.post(
                        url, headers=self.headers, timeout=30
                    )
                    response.raise_for_status()
                except Exception as sig_err:
                    logger.error(
                        f"Erro ao aprovar signatário {sig_id}: {sig_err}"
                    )
