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
            "steps",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def to_internal_value(self, data):
        if "steps" in data and isinstance(data["steps"], list):
            for step in data["steps"]:
                if "id" in step:
                    val = step["id"]
                    if isinstance(val, str) and not val.isdigit():
                        del step["id"]
                    elif val is None:
                        del step["id"]
        return super().to_internal_value(data)
