from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from shared_auth.permissions import IsSameOrganization


from inspection.providers.factory import get_provider_instance


class ProviderViewSet(viewsets.ViewSet):
    permission_classes = [IsSameOrganization]

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        provider_name = request.query_params.get("provider", "sga")
        provider = get_provider_instance(provider_name)
        data = provider.search(request, request.query_params)
        return Response(data)
