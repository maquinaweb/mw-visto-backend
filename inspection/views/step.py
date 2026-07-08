from rest_framework import filters, viewsets
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

    def get_queryset(self):
        # Filter steps where inspection is owned by the request organization
        return InspectionStep.objects.filter(
            inspection__organization_id=self.request.organization_id
        )
