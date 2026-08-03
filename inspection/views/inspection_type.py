from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from shared_auth.mixins import LoggedOrganizationMixin
from shared_auth.permissions import IsSameOrganization

from core.mixins.bulk_delete import BulkDeleteMixin
from core.mixins.soft_delete import SoftDeleteViewSetMixin
from core.pagination import TotalPagination
from core.services.s3 import S3Utils
from inspection.models.inspection_type import InspectionType
from inspection.serializers.inspection_type import InspectionTypeSerializer


class InspectionTypeViewSet(
    SoftDeleteViewSetMixin, BulkDeleteMixin, LoggedOrganizationMixin
):
    queryset = InspectionType.objects.all().order_by("-created_at")
    serializer_class = InspectionTypeSerializer
    pagination_class = TotalPagination
    permission_classes = [IsSameOrganization]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name"]

    @action(detail=False, methods=["post"], url_path="upload-url")
    def get_upload_url(self, request):
        s3 = S3Utils()
        file_data = request.data

        path = f"organization/{request.organization_id}/inspection_types"
        data = s3.presign_url(path, file_data)

        from django.conf import settings

        cloudfront = getattr(settings, "CLOUDFRONT_DOMAIN", None)
        if cloudfront:
            data["public_url"] = f"https://{cloudfront}/{data['fields']['key']}"
        else:
            data["public_url"] = (
                f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{data['fields']['key']}"
            )

        return Response(data)

    @action(detail=False, methods=["get"], url_path="vehicle-types")
    def vehicle_types(self, request):
        org_id = getattr(request, "organization_id", None)
        if not org_id:
            return Response({"results": []})

        current_id = request.query_params.get("current_id")

        # 1. Buscar tipos de veículo ativos na Hinova
        try:
            from core.services.hinova.hinova import HinovaEndPoints

            res = HinovaEndPoints(org_id).veiculo.listar_tipo_veiculo()
            hinova_types = res.json() if res and res.status_code == 200 else []
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                f"Erro ao buscar tipos de veículo na Hinova: {e}"
            )
            hinova_types = []

        # 2. Mapear códigos já atribuídos a outros tipos de vistoria
        qs = InspectionType.objects.filter(organization_id=org_id)
        if current_id:
            qs = qs.exclude(id=current_id)

        assigned = {
            str(vt.get("id") if isinstance(vt, dict) else vt): itype.name
            for itype in qs
            for vt in (itype.vehicle_types or [])
        }

        # 3. Mapear resultado formatado com status disabled
        results = []
        for item in hinova_types if isinstance(hinova_types, list) else []:
            code = str(
                item.get("codigo_tipo")
                or item.get("codigo")
                or item.get("id")
                or ""
            )
            name = str(
                item.get("descricao_tipo")
                or item.get("descricao")
                or item.get("nome")
                or ""
            )
            if not code:
                continue

            used_by = assigned.get(code)
            results.append(
                {
                    "id": code,
                    "name": f"{name} (Já usado em: {used_by})"
                    if used_by
                    else name,
                    "disabled": bool(used_by),
                }
            )

        return Response({"results": results})
