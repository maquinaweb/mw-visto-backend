from rest_framework import filters, viewsets
from shared_auth.permissions import IsSameOrganization

from core.mixins.bulk_delete import BulkDeleteMixin
from core.pagination import TotalPagination
from inspection.models.inspection_type_step import InspectionTypeStep
from inspection.serializers.inspection_type_step import (
    InspectionTypeStepSerializer,
)


class InspectionTypeStepViewSet(BulkDeleteMixin, viewsets.ModelViewSet):
    serializer_class = InspectionTypeStepSerializer
    pagination_class = TotalPagination
    permission_classes = [IsSameOrganization]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["order", "created_at"]

    def get_queryset(self):
        return InspectionTypeStep.objects.filter(
            inspection_type__organization_id=self.request.organization_id
        ).order_by("order", "created_at")
