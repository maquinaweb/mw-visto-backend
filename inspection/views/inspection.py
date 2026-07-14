from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from shared_auth.permissions import IsSameOrganization

from core.mixins.bulk_delete import BulkDeleteMixin
from core.mixins.soft_delete import SoftDeleteViewSetMixin
from core.pagination import TotalPagination
from inspection.filters.inspection import InspectionFilter
from inspection.models.inspection import Inspection
from inspection.serializers.inspection import InspectionSerializer
from inspection.serializers import (
    InspectionTypeSerializer,
    InspectionMotiveSerializer,
)


class InspectionViewSet(
    SoftDeleteViewSetMixin, BulkDeleteMixin, viewsets.ModelViewSet
):
    serializer_class = InspectionSerializer
    pagination_class = TotalPagination
    permission_classes = [IsSameOrganization]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_class = InspectionFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "scheduled_to"]

    def get_permissions(self):
        if self.action in ["by_hash", "verify", "finish"]:
            return [AllowAny()]
        return [IsSameOrganization()]

    queryset = (
        Inspection.objects.all()
        .order_by("-created_at")
        .prefetch_related("steps")
    )

    @action(detail=False, methods=["get"], url_path="default-by-last")
    def default_by_last(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        user = request.user

        inspection = queryset.filter(user_id=user.id).order_by("-id").first()

        if not inspection:
            return Response({"error": "No inspection found"}, status=404)

        from inspection.serializers.inspector import InspectorSerializer
        from sga.serializers.vehicle_sga import VehicleSGASerializer

        inspector_data = None
        if hasattr(inspection, "inspector") and inspection.inspector:
            inspector_data = InspectorSerializer(inspection.inspector).data

        vehicle_sga_data = None
        if hasattr(inspection, "vehicle_sga") and inspection.vehicle_sga:
            vehicle_sga_data = VehicleSGASerializer(inspection.vehicle_sga).data

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
                "vehicle_sga": vehicle_sga_data,
            }
        )

    @action(detail=False, methods=["get"], url_path="by_hash")
    def by_hash(self, request):
        hash_val = request.query_params.get("hash")
        if not hash_val:
            return Response({"error": "Hash is required"}, status=400)
        try:
            inspection = Inspection.objects.prefetch_related("steps").get(hash=hash_val)
            serializer = InspectionSerializer(inspection)
            return Response(serializer.data)
        except (Inspection.DoesNotExist, ValueError):
            return Response({"error": "Inspection not found"}, status=404)

    @action(detail=False, methods=["post"], url_path="verify")
    def verify(self, request):
        hash_val = request.data.get("hash")
        document = request.data.get("document")

        if not hash_val or not document:
            return Response({"error": "Hash and document are required"}, status=400)

        try:
            inspection = Inspection.objects.get(hash=hash_val)
        except (Inspection.DoesNotExist, ValueError):
            return Response({"error": "Inspection not found"}, status=404)

        import re
        norm_document = re.sub(r"\D", "", document)

        db_document = ""
        if hasattr(inspection, "inspector") and inspection.inspector and inspection.inspector.contact and inspection.inspector.contact.document:
            db_document = re.sub(r"\D", "", inspection.inspector.contact.document)

        if norm_document != db_document:
            return Response({"error": "CPF/CNPJ incorreto"}, status=400)

        return Response({"status": "success", "message": "Dados verificados com sucesso"})

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
        return Response({"status": "success", "message": "Vistoria concluída com sucesso"})
