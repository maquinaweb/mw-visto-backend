from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers
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
    signature = serializers.JSONField(
        required=False, write_only=True, allow_null=True
    )

    class Meta:
        model = Inspection
        fields = [
            "id",
            "title",
            "description",
            "status",
            "hash",
            "inspection_type",
            "motive",
            "steps",
            "inspector",
            "vehicle_sga",
            "notify_email",
            "notify_whatsapp",
            "signature_protocol_id",
            "signature_hash",
            "signature",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "hash", "created_at", "updated_at"]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.inspection_type:
            from inspection.serializers.inspection_type import (
                InspectionTypeSerializer,
            )

            ret["inspection_type"] = InspectionTypeSerializer(
                instance.inspection_type
            ).data
        return ret
