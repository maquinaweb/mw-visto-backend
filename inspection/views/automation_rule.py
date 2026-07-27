import logging

from django.core.cache import cache
from rest_framework.decorators import action
from rest_framework.response import Response
from shared_auth.mixins import LoggedOrganizationMixin
from shared_auth.permissions import IsSameOrganization

from core.mixins.soft_delete import SoftDeleteViewSetMixin
from inspection.models.automation_rule import AutomationRule
from inspection.serializers.automation_rule import (
    AutomationRuleSerializer,
)

logger = logging.getLogger(__name__)


class AutomationRuleViewSet(SoftDeleteViewSetMixin, LoggedOrganizationMixin):
    queryset = AutomationRule.objects.all().order_by("-created_at")
    serializer_class = AutomationRuleSerializer
    permission_classes = [IsSameOrganization]

    @action(detail=False, methods=["get"], url_path="situations")
    def situations(self, request, *args, **kwargs):
        org_id = getattr(request, "organization_id", None)
        if not org_id:
            return Response([])

        cache_key = f"activator_situations_org_{org_id}"

        cached_situations = cache.get(cache_key)
        if cached_situations:
            return Response(cached_situations)

        situations_list = []
        try:
            from core.services.hinova.hinova import HinovaEndPoints

            hinova = HinovaEndPoints(org_id)
            res = hinova.client.get("listar/situacao/todos")
            if res.status_code == 200:
                raw_items = res.json()
                if isinstance(raw_items, list):
                    for item in raw_items:
                        code_val = item.get("codigo_situacao")
                        desc_val = (
                            item.get("descricao_situacao")
                            or item.get("situacao")
                            or ""
                        )
                        if code_val:
                            try:
                                code_int = int(code_val)
                            except ValueError:
                                code_int = code_val
                            situations_list.append(
                                {
                                    "code": code_int,
                                    "name": f"{code_val} - {desc_val}".strip(
                                        " -"
                                    ),
                                }
                            )
        except Exception as e:
            logger.warning(
                f"Falha ao consultar situações Hinova para org {org_id}: {e}"
            )

        if situations_list:
            cache.set(cache_key, situations_list, timeout=3600)

        return Response(situations_list)
