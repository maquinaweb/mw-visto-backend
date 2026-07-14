from drf_writable_nested.serializers import WritableNestedModelSerializer
from shared_auth.serializers import OrganizationCreateSerializerMixin

from sga.models.vehicle_sga import VehicleSGA


class VehicleSGASerializer(
    OrganizationCreateSerializerMixin, WritableNestedModelSerializer
):
    class Meta:
        model = VehicleSGA
        fields = ("id", "codigo_veiculo", "codigo_evento", "plate", "chassi")
