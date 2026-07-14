from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers
from shared_auth.serializers import OrganizationCreateSerializerMixin

from sga.models.associate import Associate


class AssociateSerializer(
    OrganizationCreateSerializerMixin, WritableNestedModelSerializer
):
    codigo_associado = serializers.CharField(validators=[])

    class Meta:
        model = Associate
        fields = ("id", "codigo_beneficiario", "codigo_associado")

    def create(self, validated_data):
        org = self.context["request"].organization_id
        codigo_associado = validated_data.get("codigo_associado")
        associate, _ = Associate.objects.get_or_create(
            organization_id=org,
            codigo_associado=codigo_associado,
            defaults=validated_data,
        )

        return associate
