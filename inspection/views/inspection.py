from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
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
            }
        )
