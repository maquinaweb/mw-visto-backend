from drf_writable_nested.serializers import WritableNestedModelSerializer
from shared_auth.serializers import OrganizationUserCreateSerializerMixin

from inspection.models.inspection_type import InspectionType
from inspection.serializers.inspection_type_step import (
    InspectionTypeStepSerializer,
)


class InspectionTypeSerializer(
    WritableNestedModelSerializer, OrganizationUserCreateSerializerMixin
):
    steps = InspectionTypeStepSerializer(many=True, required=False)

    class Meta:
        model = InspectionType
        fields = [
            "id",
            "name",
            "description",
            "expiration_days",
            "expiration_hours",
            "steps",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
