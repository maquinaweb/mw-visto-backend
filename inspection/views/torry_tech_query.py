from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from shared_auth.permissions import IsSameOrganization

from core.pagination import TotalPagination
from inspection.models.torry_tech_query import TorryTechQuery
from inspection.serializers.torry_tech_query import TorryTechQuerySerializer
from inspection.filters.torry_tech_query import TorryTechQueryFilter


class TorryTechQueryViewSet(viewsets.ModelViewSet):
    serializer_class = TorryTechQuerySerializer
    pagination_class = TotalPagination
    permission_classes = [IsSameOrganization]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = TorryTechQueryFilter
    ordering_fields = ["created_at"]

    def get_queryset(self):
        if (
            hasattr(self.request, "organization_id")
            and self.request.organization_id
        ):
            return TorryTechQuery.objects.filter(
                organization_id=self.request.organization_id
            )
        return TorryTechQuery.objects.none()

    def create(self, request, *args, **kwargs):
        inspection_id = request.data.get("inspection")
        if not inspection_id:
            return Response(
                {"error": "O campo inspection (ID da vistoria) é obrigatório."},
                status=400,
            )

        try:
            from inspection.models.inspection import Inspection

            inspection = Inspection.objects.get(id=inspection_id)
        except (Inspection.DoesNotExist, ValueError):
            return Response({"error": "Vistoria não encontrada."}, status=404)

        # Check permissions for this inspection
        self.check_object_permissions(request, inspection)

        cons = request.data.get("cons", "83")
        uf = request.data.get("uf", "")

        from inspection.services.torry_tech_service import TorryTechService

        query = TorryTechService.request_query(inspection, cons=cons, uf=uf)

        serializer = self.get_serializer(query)
        return Response(serializer.data, status=201)

    @action(detail=True, methods=["post"], url_path="refresh")
    def refresh(self, request, pk=None):
        query = self.get_object()

        from inspection.services.torry_tech_service import TorryTechService

        query = TorryTechService.refresh_query(query)

        serializer = self.get_serializer(query)
        return Response(serializer.data)
