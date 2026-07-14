from drf_writable_nested.serializers import WritableNestedModelSerializer
from shared_auth.serializers import OrganizationUserCreateSerializerMixin

from inspection.models.inspection import Inspection
from inspection.serializers.step import InspectionStepSerializer
from inspection.serializers.inspector import InspectorSerializer
from sga.serializers.vehicle_sga import VehicleSGASerializer


class InspectionSerializer(
    WritableNestedModelSerializer, OrganizationUserCreateSerializerMixin
):
    steps = InspectionStepSerializer(many=True, required=False)
    inspector = InspectorSerializer(required=False, allow_null=True)
    vehicle_sga = VehicleSGASerializer(required=False, allow_null=True)

    class Meta:
        model = Inspection
        fields = [
            "id",
            "title",
            "description",
            "status",
            "hash",
            "scheduled_to",
            "inspection_type",
            "motive",
            "steps",
            "inspector",
            "vehicle_sga",
            "notify_email",
            "notify_whatsapp",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "hash", "created_at", "updated_at"]
