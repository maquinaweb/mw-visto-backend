from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
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
        if self.action in ["partial_update", "retrieve", "create", "rotate"]:
            return [AllowAny()]
        return [IsSameOrganization()]

    def create(self, request, *args, **kwargs):
        hash_val = request.query_params.get("hash")
        inspection_id = request.data.get("inspection")
        if not hash_val or not inspection_id:
            from rest_framework.response import Response

            return Response(
                {"error": "Hash e id da vistoria são obrigatórios"}, status=400
            )

        try:
            from inspection.models.inspection import Inspection

            Inspection.objects.get(id=inspection_id, hash=hash_val)
        except (Inspection.DoesNotExist, ValueError):
            from rest_framework.response import Response

            return Response(
                {"error": "Vistoria inválida ou hash incorreto"}, status=400
            )

        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        hash_val = self.request.query_params.get("hash")
        if hash_val and self.action in [
            "partial_update",
            "retrieve",
            "create",
            "rotate",
        ]:
            try:
                return InspectionStep.objects.filter(inspection__hash=hash_val)
            except ValueError:
                return InspectionStep.objects.none()

        if (
            hasattr(self.request, "organization_id")
            and self.request.organization_id
        ):
            return InspectionStep.objects.filter(
                inspection__organization_id=self.request.organization_id
            )
        return InspectionStep.objects.none()

    @action(detail=True, methods=["post"], permission_classes=[AllowAny])
    def rotate(self, request, pk=None):
        step = self.get_object()
        if not step.file:
            return Response(
                {"error": "Nenhuma imagem associada a este passo"}, status=400
            )

        try:
            degrees = int(request.data.get("degrees", 90))
        except (ValueError, TypeError):
            return Response({"error": "Graus de rotação inválidos"}, status=400)

        if degrees not in [90, 180, 270]:
            return Response(
                {"error": "Graus de rotação devem ser 90, 180 ou 270"},
                status=400,
            )

        from io import BytesIO
        from PIL import Image
        from django.core.files.base import ContentFile

        try:
            step.file.open("rb")
            img = Image.open(step.file)

            ccw_degrees = (360 - degrees) % 360

            if ccw_degrees == 90:
                img_rotated = img.transpose(Image.ROTATE_90)
            elif ccw_degrees == 180:
                img_rotated = img.transpose(Image.ROTATE_180)
            elif ccw_degrees == 270:
                img_rotated = img.transpose(Image.ROTATE_270)
            else:
                img_rotated = img.rotate(ccw_degrees, expand=True)

            img_format = img.format or "JPEG"
            out_bytes = BytesIO()
            img_rotated.save(out_bytes, format=img_format)
            out_bytes.seek(0)

            old_file_name = step.file.name

            step.file.save(
                f"rotated_{degrees}.{img_format.lower()}",
                ContentFile(out_bytes.read()),
                save=True,
            )

            if old_file_name:
                try:
                    step.file.storage.delete(old_file_name)
                except Exception:
                    pass

            return Response(
                {
                    "message": "Imagem rotacionada com sucesso",
                    "file": step.file.url,
                }
            )

        except Exception as e:
            return Response(
                {"error": f"Erro ao processar imagem: {str(e)}"}, status=500
            )
