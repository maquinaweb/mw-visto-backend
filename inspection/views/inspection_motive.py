from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from shared_auth.mixins import LoggedOrganizationMixin
from shared_auth.permissions import IsSameOrganization

from core.mixins.bulk_delete import BulkDeleteMixin
from core.mixins.soft_delete import SoftDeleteViewSetMixin
from core.pagination import TotalPagination
from inspection.models.inspection_motive import InspectionMotive
from inspection.serializers.inspection_motive import InspectionMotiveSerializer


class InspectionMotiveViewSet(
    SoftDeleteViewSetMixin, BulkDeleteMixin, LoggedOrganizationMixin
):
    queryset = InspectionMotive.objects.all().order_by("-created_at")
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
