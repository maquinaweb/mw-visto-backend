from rest_framework import serializers
from shared_auth.serializers import OrganizationCreateSerializerMixin
from inspection.models.torry_tech_query import TorryTechQuery


class TorryTechQuerySerializer(
    OrganizationCreateSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = TorryTechQuery
        fields = [
            "id",
            "inspection",
            "plate",
            "chassi",
            "cons",
            "uf",
            "id_pesquisa",
            "status_consulta",
            "success",
            "message",
            "response_data",
            "link_impressao",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
