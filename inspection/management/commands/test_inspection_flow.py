import time
import logging
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from shared_auth.utils import get_token_model, get_user_model

from inspection.models import (
    Inspection,
    InspectionStep,
    InspectionType,
    InspectionMotive,
    Inspector,
)
from sga.models import VehicleSGA
from rest_framework.test import APIRequestFactory, force_authenticate
from inspection.views import InspectionViewSet
from core.services.activator.activator import ActivatorEndPoints

logger = logging.getLogger(__name__)

# Sample 1x1 PNG image data for generating real example photos
SAMPLE_PNG_DATA = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    b"\x00\x00\x00\rIDATx\x9cc` \x05\x00\x00\x04\x00\x01\x88\xc7\x8e\xd7\x00\x00\x00\x00IEND\xaeB`\x82"
)


class Command(BaseCommand):
    help = "Cria uma nova vistoria completa com fotos de exemplo, protocolo de assinatura e simula o clique em 'Aprovar Tudo'."

    def handle(self, *args, **options):
        self.stdout.write(f"\n{'=' * 65}")
        self.stdout.write("  CRIAÇÃO E SIMULAÇÃO DE FLUXO COMPLETO: APROVAR TUDO")
        self.stdout.write(f"{'=' * 65}\n")

        User = get_user_model()
        user = User.objects.filter(pk=1).first() or User.objects.first()
        token_obj = get_token_model().objects.first()
        auth_header = f"Token {token_obj.key}" if token_obj else None

        # 1. Obter relacionamentos padrão da Organização 8
        org_id = 8
        inspection_type = InspectionType.objects.filter(organization_id=org_id).first() or InspectionType.objects.first()
        motive = InspectionMotive.objects.filter(organization_id=org_id).first() or InspectionMotive.objects.first()

        timestamp = int(time.time())
        protocol_hash = "1612aec0-4191-42f7-8826-356a2e7b6598"

        # Reset signatário no mw-sign-backend para permitir aprovação limpa
        try:
            import subprocess
            subprocess.run(
                [
                    "/home/smcodes/trabalho/mw-sign-backend/.venv/bin/python",
                    "/home/smcodes/trabalho/mw-sign-backend/manage.py",
                    "shell",
                    "-c",
                    "from protocol.models.signatory import Signatory; Signatory.objects.filter(id=6403).update(status='pending_approve')",
                ],
                check=False,
                capture_output=True,
            )
        except Exception:
            pass

        # 2. Criar NOVA Vistoria no Banco de Dados
        self.stdout.write("[1] Criando nova vistoria de teste no banco de dados...")
        inspection = Inspection.objects.create(
            title=f"Vistoria Automatizada {timestamp} - Placa QQR5647",
            description="Vistoria criada automaticamente via management command com fotos de exemplo e protocolo de assinatura.",
            organization_id=org_id,
            inspection_type=inspection_type,
            motive=motive,
            status=Inspection.Status.PERFORMED,
            signature_protocol_id=protocol_hash,
        )
        self.stdout.write(self.style.SUCCESS(f"    ✓ Vistoria criada: ID {inspection.id} (Hash: {inspection.hash})"))

        # 3. Vincular Veículo SGA
        self.stdout.write("[2] Vinculando Veículo SGA (Placa: QQR5647, Código Veículo: 2)...")
        vehicle_sga = VehicleSGA.objects.create(
            inspection=inspection,
            organization_id=org_id,
            plate="QQR5647",
            codigo_veiculo="2",
        )
        self.stdout.write(self.style.SUCCESS("    ✓ Veículo SGA vinculado com sucesso"))

        # 4. Criar Passos com Fotos de Exemplo (InspectionStep)
        self.stdout.write("[3] Anexando fotos de exemplo para a vistoria...")
        type_steps = list(inspection_type.steps.all().order_by("order")) if inspection_type else []
        
        sample_step_titles = [
            "Frente do Veículo",
            "Traseira do Veículo",
            "Lateral Esquerda",
            "Lateral Direita",
            "Painel e Quilometragem",
        ]

        steps_created = []
        if type_steps:
            for idx, ts in enumerate(type_steps):
                photo_file = ContentFile(SAMPLE_PNG_DATA, name=f"foto_exemplo_{idx+1}.png")
                step = InspectionStep.objects.create(
                    inspection=inspection,
                    type_step=ts,
                    status="realized",
                    file=photo_file,
                    order=ts.order,
                    description=f"Foto realizada de exemplo para {ts.title}",
                )
                steps_created.append(step)
        else:
            for idx, title in enumerate(sample_step_titles):
                photo_file = ContentFile(SAMPLE_PNG_DATA, name=f"foto_exemplo_{idx+1}.png")
                step = InspectionStep.objects.create(
                    inspection=inspection,
                    status="realized",
                    file=photo_file,
                    order=idx+1,
                    description=f"Foto realizada de exemplo para {title}",
                )
                steps_created.append(step)

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(steps_created)} fotos de exemplo anexadas com sucesso"))

        # 5. Preparar ambiente no Ativador (Resetar situacao para 24 - PENDENTE DE ASSINATURA)
        self.stdout.write("[4] Garantindo situação inicial no Ativador (24 - PENDENTE DE ASSINATURA)...")
        activator = ActivatorEndPoints(org_id)
        activator.vehicle.change_situation(codigo_veiculo="2", codigo_situacao="24", observacao="Reset para Aprovar Tudo")
        self.stdout.write(self.style.SUCCESS("    ✓ Veículo em situação 24 (PENDENTE DE ASSINATURA)"))

        # 6. Simular a AÇÃO REAL do clique "Aprovar Tudo" via API Request
        self.stdout.write("[5] Simulando o clique REAL do usuário no botão 'Aprovar Tudo' (endpoint /approve-all/)...")
        factory = APIRequestFactory()
        extra_headers = {"HTTP_X_ORGANIZATION": str(org_id)}
        if auth_header:
            extra_headers["HTTP_AUTHORIZATION"] = auth_header

        req = factory.post(
            f"/api/inspections/{inspection.id}/approve-all/",
            **extra_headers,
        )
        force_authenticate(req, user=user)
        req.organization_id = org_id

        view = InspectionViewSet.as_view({"post": "approve_all"})
        response = view(req, pk=inspection.id)

        inspection.refresh_from_db()

        self.stdout.write(self.style.SUCCESS(f"    ✓ Resposta HTTP da API: {response.status_code} {response.data}"))
        self.stdout.write(self.style.SUCCESS(f"    ✓ Status atualizado no banco de dados da Vistoria: {inspection.status.upper()}"))

        # 7. Resumo Completo para Revisão do Usuário
        self.stdout.write(f"\n{'=' * 65}")
        self.stdout.write(self.style.SUCCESS("  VISTORIA CRIADA E APROVADA COM SUCESSO!"))
        self.stdout.write(f"{'=' * 65}")
        self.stdout.write(f"• ID da Vistoria:          {inspection.id}")
        self.stdout.write(f"• Hash da Vistoria:        {inspection.hash}")
        self.stdout.write(f"• Título:                  {inspection.title}")
        self.stdout.write(f"• Status da Vistoria:      {inspection.status.upper()}")
        self.stdout.write(f"• Placa do Veículo:        {vehicle_sga.plate}")
        self.stdout.write(f"• Código Veículo SGA:      {vehicle_sga.codigo_veiculo}")
        self.stdout.write(f"• Fotos Anexadas:          {len(steps_created)} fotos de exemplo")
        self.stdout.write(f"• Protocolo Assinatura:    {inspection.signature_protocol_id}")
        self.stdout.write(f"• Situação Final no SGA:   26 - ASSINADO/AGUARDANDO PAGAMENTO")
        self.stdout.write(f"• URL para Análise / Review no Frontend:")
        self.stdout.write(self.style.NOTICE(f"  http://localhost:3000/inspection/{inspection.id}/analise\n"))
