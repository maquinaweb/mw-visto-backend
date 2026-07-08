from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from shared_auth.permissions import IsSameOrganization

from core.mixins.bulk_delete import BulkDeleteMixin
from core.mixins.soft_delete import SoftDeleteViewSetMixin
from core.pagination import TotalPagination
from inspection.filters.inspection import InspectionFilter
from inspection.models.inspection import Inspection
from inspection.serializers.inspection import InspectionSerializer


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

    queryset = (
        Inspection.objects.all()
        .order_by("-created_at")
        .prefetch_related("steps")
    )
