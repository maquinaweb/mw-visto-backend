from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from shared_auth.permissions import IsSameOrganization

from core.mixins.bulk_delete import BulkDeleteMixin
from core.mixins.soft_delete import SoftDeleteViewSetMixin
from core.pagination import TotalPagination
from inspection.models.inspection_motive import InspectionMotive
from inspection.serializers.inspection_motive import InspectionMotiveSerializer


class InspectionMotiveViewSet(
    SoftDeleteViewSetMixin, BulkDeleteMixin, viewsets.ModelViewSet
):
    serializer_class = InspectionMotiveSerializer
    pagination_class = TotalPagination
    permission_classes = [IsSameOrganization]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name"]

    def get_queryset(self):
        return InspectionMotive.objects.filter(
            organization_id=self.request.organization_id
        ).order_by("-created_at")
