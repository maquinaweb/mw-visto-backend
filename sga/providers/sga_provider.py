from rest_framework.exceptions import ValidationError

from core.services.hinova.hinova import HinovaEndPoints
from inspection.providers.base import BaseProvider
from message.models.contact import Contact


class SGAProvider(BaseProvider):
    def search(self, request, query_params: dict) -> dict:
        plate = query_params.get("plate")
        chassi = query_params.get("chassi")
        codigo_associado = query_params.get("codigo_associado")

        if not plate and not chassi and not codigo_associado:
            raise ValidationError(
                "Informe a placa, chassi ou o código de associado."
            )

        hinova_endpoints = HinovaEndPoints(request.organization_id)
        associate = None
        vehicle_data = {}

        # 1. Search in SGA/Hinova
        if codigo_associado:
            res_assoc, status_code = hinova_endpoints.associado.buscar_codigo(
                codigo_associado
            )
            if status_code >= 400:
                raise ValidationError("Associado não encontrado.")
            associate = res_assoc
        elif plate:
            veiculo_response = hinova_endpoints.veiculo.buscar(plate)
            if (
                veiculo_response.status_code >= 400
                or not veiculo_response.json()
            ):
                raise ValidationError(
                    "Veículo não encontrado pela placa informada."
                )

            vehicle_data = veiculo_response.json()[0]
            cod_assoc = vehicle_data.get("codigo_associado")
            if not cod_assoc:
                raise ValidationError(
                    "Associado não encontrado para este veículo."
                )

            res_assoc, status_code = hinova_endpoints.associado.buscar_codigo(
                cod_assoc
            )
            if status_code >= 400:
                raise ValidationError("Associado não encontrado.")
            associate = res_assoc
        elif chassi:
            veiculo_response = hinova_endpoints.veiculo.buscar_chassi(chassi)
            if (
                veiculo_response.status_code >= 400
                or not veiculo_response.json()
            ):
                raise ValidationError(
                    "Veículo não encontrado pelo chassi informado."
                )

            vehicle_data = veiculo_response.json()[0]
            cod_assoc = vehicle_data.get("codigo_associado")
            if not cod_assoc:
                raise ValidationError(
                    "Associado não encontrado para este veículo."
                )

            res_assoc, status_code = hinova_endpoints.associado.buscar_codigo(
                cod_assoc
            )
            if status_code >= 400:
                raise ValidationError("Associado não encontrado.")
            associate = res_assoc

        if not associate:
            raise ValidationError("Nenhum dado encontrado.")

        # Check if we already have this contact in our DB
        contact = (
            Contact.objects.select_related("associate")
            .filter(
                associate__codigo_associado=associate.get("codigo_associado")
            )
            .first()
        )

        # Format output structure to match frontend
        return {
            "contact": {
                "id": contact.id if contact else None,
                "name": associate.get("nome"),
                "email": associate.get("email"),
                "phone": associate.get("celular") or associate.get("telefone"),
                "document": associate.get("cpf") or associate.get("cnpj"),
                "associate": {
                    "id": contact.associate.id
                    if contact and hasattr(contact, "associate")
                    else None,
                    "codigo_associado": associate.get("codigo_associado"),
                    "codigo_beneficiario": associate.get("codigo_beneficiario"),
                },
            },
            "vehicle_sga": {
                "plate": vehicle_data.get("placa") or plate or "",
                "chassi": vehicle_data.get("chassi") or chassi or "",
                "codigo_veiculo": vehicle_data.get("codigo_veiculo") or "",
                "codigo_evento": vehicle_data.get("codigo_evento") or "",
            },
        }
