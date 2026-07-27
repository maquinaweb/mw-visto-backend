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
