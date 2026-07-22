import logging
import urllib.parse
from rest_framework.exceptions import ValidationError
from signature.services.signature import SignatureService

logger = logging.getLogger(__name__)


def process_signature_integration(request, inspection, signature_data):
    term = signature_data.get("term")

    if not term:
        return

    try:
        auth_header = request.headers.get("Authorization")
        org_header = request.headers.get("X-Organization")
        sig_service = SignatureService(
            auth_header=auth_header, org_header=org_header
        )

        inspector_data = request.data.get("inspector") or {}
        contact_data = (inspector_data).get("contact") or {}
        vehicle_sga_data = request.data.get("vehicle_sga") or {}

        # 1. Emit term PDF inside SGA via mw-sign-backend
        associate_raw = contact_data.get("associate")
        associate_data = associate_raw or {}
        doc = sig_service.create_term_pdf(
            term_code=term.get("codigo_sga"),
            associate_code=associate_data.get("codigo_associado", ""),
            beneficiary_code=associate_data.get("codigo_beneficiario", ""),
            vehicle_code=vehicle_sga_data.get("codigo_veiculo"),
            event_code=vehicle_sga_data.get("codigo_evento"),
            plate=vehicle_sga_data.get("plate"),
            tool_name=term.get("ferramenta"),
        )

        plate_val = vehicle_sga_data.get("plate")
        inspector_name = contact_data.get("name")
        term_name = term.get("nome")

        protocol_name = " - ".join(
            filter(None, [plate_val, inspector_name, term_name])
        )
        file_name = (
            f"{plate_val or inspector_name or 'documento'} - {term_name}.pdf"
        )

        # Build authentications list
        authentications = []
        if signature_data.get("auth_document"):
            authentications.append({"type": "document_identify"})
        if signature_data.get("auth_selfie"):
            authentications.append({"type": "selfie"})
        if signature_data.get("auth_manual"):
            authentications.append({"type": "manual_approval"})
        if signature_data.get("auth_email"):
            authentications.append({"type": "email"})
        if signature_data.get("auth_sms"):
            authentications.append({"type": "sms"})

        # 2. Build signatories & documents payload
        signatories = [
            {
                "type": "signer",
                "contact": {
                    "name": contact_data.get("name"),
                    "email": contact_data.get("email"),
                    "phone": contact_data.get("phone"),
                    "document": contact_data.get("document"),
                    "associate": {
                        "codigo_associado": associate_data.get(
                            "codigo_associado"
                        ),
                        "codigo_beneficiario": associate_data.get(
                            "codigo_beneficiario"
                        ),
                    }
                    if associate_raw
                    else None,
                },
                "authentications": authentications,
            }
        ]

        file_url = f"{doc.get('link_pdf')}#{urllib.parse.quote(file_name)}"
        documents = [
            {
                "file_original": file_url,
                "sga_term": term.get("id"),
                "name": file_name,
                "order": 0,
                "vehicle_sga": {
                    "plate": vehicle_sga_data.get("plate"),
                    "codigo_veiculo": vehicle_sga_data.get("codigo_veiculo")
                    or "",
                    "codigo_evento": vehicle_sga_data.get("codigo_evento")
                    or "",
                }
                if vehicle_sga_data.get("plate")
                else None,
            }
        ]

        protocol_payload = {
            "name": protocol_name,
            "signatories": signatories,
            "documents": documents,
        }

        # 3. Create protocol
        protocol = sig_service.create_protocol(protocol_payload)
        protocol_id = protocol.get("id")
        protocol_hash = protocol.get("hash")

        # 4. Map signature positions
        try:
            term_positions = sig_service.get_term_positions(term.get("id"))
            positions_data = [
                {
                    **pos,
                    "document": protocol.get("documents", [{}])[0].get("id"),
                    "signatory": protocol.get("signatories", [{}])[0].get("id"),
                }
                for pos in term_positions
            ]
            sig_service.update_protocol_positions(protocol_id, positions_data)
        except Exception as e:
            logger.error(
                f"Error mapping signature positions: {e}", exc_info=True
            )

        # 5. Send email notification if needed
        if request.data.get("notify_email"):
            try:
                sig_service.send_signature_notification(protocol_id, "email")
            except Exception as e:
                logger.error(
                    f"Error sending email signature notification: {e}",
                    exc_info=True,
                )

        # Update inspection details
        inspection.signature_protocol_id = protocol_hash
        signatories_list = protocol.get("signatories", [])
        inspection.signature_hash = (
            signatories_list[0].get("sign_hash") if signatories_list else None
        )
        inspection.save()

    except Exception as e:
        logger.error(f"Error creating signature protocol: {e}", exc_info=True)
        raise ValidationError(
            {
                "signature_protocol": f"Falha ao gerar o termo no MW Sign: {str(e)}"
            }
        )


def approve_inspection_signature_process(
    request, inspection, is_approve_all=False
):
    """
    Aprova os signatários do protocolo no MW Sign e atualiza o estado no Ativador.
    """
    if not (
        hasattr(inspection, "signature_protocol_id")
        and inspection.signature_protocol_id
    ):
        return

    try:
        auth_header = request.headers.get("Authorization")
        org_header = request.headers.get("X-Organization")
        sig_service = SignatureService(
            auth_header=auth_header, org_header=org_header
        )
        sig_service.approve_protocol_signatories(
            inspection.signature_protocol_id
        )

        from inspection.services.activator_sync import (
            sync_signature_approval_with_activator,
        )

        sync_signature_approval_with_activator(
            inspection, is_approve_all=is_approve_all
        )
    except Exception as e:
        logger.error(f"Erro ao processar aprovação de assinatura: {e}")
        raise
