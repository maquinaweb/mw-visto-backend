from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from shared_auth.permissions import IsSameOrganization
from sga.providers.sga_provider import SGAProvider


class AssociateViewSet(viewsets.ViewSet):
    permission_classes = [IsSameOrganization]

    @action(detail=False, methods=["get"])
    def search(self, request):
        provider = SGAProvider()
        data = provider.search(request, request.query_params)
        return Response(data)

    @action(detail=False, methods=["get"], url_path="search-events")
    def search_events(self, request):
        plate = request.query_params.get("plate")
        if not plate:
            raise ValidationError("Informe a placa do veículo.")

        from core.services.hinova.hinova import HinovaEndPoints

        response = HinovaEndPoints(
            request.organization_id
        ).veiculo.listar_eventos(plate)

        if response.status_code >= 400:
            error = HinovaEndPoints.handle_error(response)
            raise ValidationError(error)

        return Response(response.json())
