from rest_framework import filters, viewsets
from rest_framework.permissions import AllowAny
from shared_auth.permissions import IsSameOrganization

from core.mixins.bulk_delete import BulkDeleteMixin
from core.pagination import TotalPagination
from inspection.models.step import InspectionStep
from inspection.serializers.step import InspectionStepSerializer


class InspectionStepViewSet(BulkDeleteMixin, viewsets.ModelViewSet):
    serializer_class = InspectionStepSerializer
    pagination_class = TotalPagination
    permission_classes = [IsSameOrganization]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["order", "created_at"]

    def get_permissions(self):
        if self.action in ["partial_update", "retrieve", "create"]:
            return [AllowAny()]
        return [IsSameOrganization()]

    def create(self, request, *args, **kwargs):
        hash_val = request.query_params.get("hash")
        inspection_id = request.data.get("inspection")
        if not hash_val or not inspection_id:
            from rest_framework.response import Response
            return Response({"error": "Hash e id da vistoria são obrigatórios"}, status=400)

        try:
            from inspection.models.inspection import Inspection
            Inspection.objects.get(id=inspection_id, hash=hash_val)
        except (Inspection.DoesNotExist, ValueError):
            from rest_framework.response import Response
            return Response({"error": "Vistoria inválida ou hash incorreto"}, status=400)

        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        hash_val = self.request.query_params.get("hash")
        if hash_val and self.action in ["partial_update", "retrieve", "create"]:
            try:
                return InspectionStep.objects.filter(inspection__hash=hash_val)
            except ValueError:
                return InspectionStep.objects.none()

        if hasattr(self.request, "organization_id") and self.request.organization_id:
            return InspectionStep.objects.filter(
                inspection__organization_id=self.request.organization_id
            )
        return InspectionStep.objects.none()
