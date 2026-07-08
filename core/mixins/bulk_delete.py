from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action


class BulkDeleteMixin:
    @action(detail=False, methods=["delete"])
    def bulk_delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])

        if not ids:
            return Response(
                {"detail": "Nenhum ID fornecido."}, status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(pk__in=ids)

        if not queryset.exists():
            return Response(
                {"detail": "Nenhum dos IDs fornecidos foi encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = queryset.delete()

        return Response(
            {"detail": f"{count} objetos deletados com sucesso."},
            status=status.HTTP_204_NO_CONTENT,
        )
