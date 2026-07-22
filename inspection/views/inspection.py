import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from shared_auth.permissions import IsSameOrganization

from core.mixins.bulk_delete import BulkDeleteMixin
from core.mixins.soft_delete import SoftDeleteViewSetMixin
from core.pagination import TotalPagination
from inspection.filters.inspection import InspectionFilter
from inspection.models.inspection import Inspection
from inspection.serializers import (
    InspectionMotiveSerializer,
    InspectionTypeSerializer,
)
from inspection.serializers.inspection import InspectionSerializer

from shared_auth.mixins import LoggedOrganizationMixin

logger = logging.getLogger(__name__)


class InspectionViewSet(
    SoftDeleteViewSetMixin, BulkDeleteMixin, LoggedOrganizationMixin
):
    queryset = (
        Inspection.objects.all()
        .order_by("-created_at")
        .prefetch_related("steps")
    )
    serializer_class = InspectionSerializer
    pagination_class = TotalPagination

    def perform_create(self, serializer):
        signature_data = serializer.validated_data.pop("signature", None) or {}
        instance = serializer.save()

        if signature_data and signature_data.get("term"):
            from signature.services.integration import (
                process_signature_integration,
            )

            process_signature_integration(
                self.request, instance, signature_data
            )

        from inspection.services.activator_sync import (
            sync_inspection_with_activator,
        )

        sync_inspection_with_activator(instance)

    permission_classes = [IsSameOrganization]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_class = InspectionFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at"]

    def get_permissions(self):
        if self.action in ["by_hash", "verify", "finish"]:
            return [AllowAny()]
        return [IsSameOrganization()]

    @action(detail=False, methods=["get"], url_path="default-by-last")
    def default_by_last(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        user = request.user

        inspection = queryset.filter(user_id=user.id).order_by("-id").first()

        if not inspection:
            return Response({"error": "No inspection found"}, status=404)

        from inspection.serializers.inspector import InspectorSerializer

        inspector_data = None
        if hasattr(inspection, "inspector") and inspection.inspector:
            inspector_data = InspectorSerializer(inspection.inspector).data

        create_signature_protocol = False
        protocol_data = None
        signature_auth_document = False
        signature_auth_selfie = False
        signature_auth_manual = False
        signature_auth_email = False
        signature_auth_sms = False

        if (
            hasattr(inspection, "signature_protocol_id")
            and inspection.signature_protocol_id
        ):
            create_signature_protocol = True
            try:
                from signature.services.signature import SignatureService

                auth_header = request.headers.get("Authorization")
                org_header = request.headers.get("X-Organization")
                sig_service = SignatureService(
                    auth_header=auth_header, org_header=org_header
                )
                protocol_data = sig_service.get_protocol_by_hash(
                    inspection.signature_protocol_id
                )
                if protocol_data:
                    signatories = protocol_data.get("signatories") or []
                    if signatories:
                        auths = signatories[0].get("authentications") or []
                        auth_types = {
                            a.get("type") for a in auths if a.get("type")
                        }
                        signature_auth_document = (
                            "document_identify" in auth_types
                        )
                        signature_auth_selfie = "selfie" in auth_types
                        signature_auth_manual = "manual_approval" in auth_types
                        signature_auth_email = "email" in auth_types
                        signature_auth_sms = "sms" in auth_types
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(
                    f"Error fetching defaults from mw-sign-backend: {e}"
                )

        signature = None
        if create_signature_protocol:
            term_id = None
            if protocol_data:
                documents = protocol_data.get("documents") or []
                if documents:
                    term_id = documents[0].get("sga_term")

            signature = {
                "term": {"id": term_id} if term_id else None,
                "auth_document": signature_auth_document,
                "auth_selfie": signature_auth_selfie,
                "auth_manual": signature_auth_manual,
                "auth_email": signature_auth_email,
                "auth_sms": signature_auth_sms,
            }

        return Response(
            {
                "inspection_type": InspectionTypeSerializer(
                    inspection.inspection_type
                ).data
                if inspection.inspection_type
                else None,
                "motive": InspectionMotiveSerializer(inspection.motive).data
                if inspection.motive
                else None,
                "notify_email": inspection.notify_email,
                "notify_whatsapp": inspection.notify_whatsapp,
                "inspector": inspector_data,
                "signature": signature,
            }
        )

    @action(detail=False, methods=["get"], url_path="by_hash")
    def by_hash(self, request):
        hash_val = request.query_params.get("hash")
        if not hash_val:
            return Response({"error": "Hash is required"}, status=400)
        try:
            inspection = Inspection.objects.prefetch_related("steps").get(
                hash=hash_val
            )
            serializer = InspectionSerializer(inspection)
            return Response(serializer.data)
        except (Inspection.DoesNotExist, ValueError):
            return Response({"error": "Inspection not found"}, status=404)

    @action(detail=False, methods=["post"], url_path="verify")
    def verify(self, request):
        hash_val = request.data.get("hash")
        document = request.data.get("document")

        if not hash_val or not document:
            return Response(
                {"error": "Hash and document are required"}, status=400
            )

        try:
            inspection = Inspection.objects.get(hash=hash_val)
        except (Inspection.DoesNotExist, ValueError):
            return Response({"error": "Inspection not found"}, status=404)

        import re

        norm_document = re.sub(r"\D", "", document)

        db_document = ""
        if (
            hasattr(inspection, "inspector")
            and inspection.inspector
            and inspection.inspector.contact
            and inspection.inspector.contact.document
        ):
            db_document = re.sub(
                r"\D", "", inspection.inspector.contact.document
            )

        if norm_document != db_document:
            return Response({"error": "CPF/CNPJ incorreto"}, status=400)

        return Response(
            {"status": "success", "message": "Dados verificados com sucesso"}
        )

    @action(detail=True, methods=["post"], url_path="finish")
    def finish(self, request, pk=None):
        try:
            inspection = Inspection.objects.get(hash=pk)
        except (Inspection.DoesNotExist, ValueError):
            try:
                inspection = Inspection.objects.get(id=pk)
            except (Inspection.DoesNotExist, ValueError):
                return Response({"error": "Inspection not found"}, status=404)

        inspection.status = Inspection.Status.PERFORMED
        inspection.save()
        return Response(
            {"status": "success", "message": "Vistoria concluída com sucesso"}
        )

    @action(detail=True, methods=["post"], url_path="analyze")
    def analyze(self, request, pk=None):
        inspection = self.get_object()
        from inspection.tasks import analyze_steps_task

        analyze_steps_task(inspection.id)
        return Response(
            {
                "status": "success",
                "message": "Análise de IA das etapas iniciada.",
            }
        )

    @action(detail=True, methods=["post"], url_path="approve-all")
    def approve_all(self, request, pk=None):
        inspection = self.get_object()

        # 1. Aprovar a vistoria (o save() altera para APROVADO_PARA_CORRECAO / 30 no Ativador)
        inspection.status = Inspection.Status.APPROVED
        inspection.save()

        # 2. Se houver protocolo de assinatura, aprova os signatários e avança no Ativador
        from signature.services.integration import (
            approve_inspection_signature_process,
        )

        approve_inspection_signature_process(
            request, inspection, is_approve_all=True
        )

        return Response(
            {
                "status": "success",
                "message": "Vistoria e assinatura aprovadas com sucesso.",
            }
        )

    @action(detail=True, methods=["post"], url_path="approve-signature")
    def approve_signature(self, request, pk=None):
        inspection = self.get_object()
        if inspection.status != Inspection.Status.APPROVED:
            return Response(
                {
                    "error": "A vistoria precisa ser aprovada antes de aprovar a assinatura."
                },
                status=400,
            )

        from signature.services.integration import (
            approve_inspection_signature_process,
        )

        try:
            approve_inspection_signature_process(
                request, inspection, is_approve_all=False
            )
        except Exception:
            return Response(
                {"error": "Erro ao aprovar assinatura."}, status=500
            )

        return Response(
            {"status": "success", "message": "Assinatura aprovada com sucesso."}
        )
