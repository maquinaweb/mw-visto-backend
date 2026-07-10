from drf_writable_nested.serializers import WritableNestedModelSerializer
from shared_auth.serializers import OrganizationUserCreateSerializerMixin

from inspection.models.inspection_type import InspectionType
from inspection.serializers.inspection_motive import InspectionMotiveSerializer
from inspection.serializers.inspection_type_step import (
    InspectionTypeStepSerializer,
)


class InspectionTypeSerializer(
    WritableNestedModelSerializer, OrganizationUserCreateSerializerMixin
):
    steps = InspectionTypeStepSerializer(many=True, required=False)
    motive_detail = InspectionMotiveSerializer(source="motive", read_only=True)

    class Meta:
        model = InspectionType
        fields = [
            "id",
            "name",
            "description",
            "motive",
            "motive_detail",
            "steps",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
