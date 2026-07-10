from drf_writable_nested.serializers import WritableNestedModelSerializer
from shared_auth.serializers import OrganizationUserCreateSerializerMixin

from inspection.models.inspection import Inspection
from inspection.serializers.step import InspectionStepSerializer


class InspectionSerializer(
    WritableNestedModelSerializer, OrganizationUserCreateSerializerMixin
):
    steps = InspectionStepSerializer(many=True, required=False)

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
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "hash", "created_at", "updated_at"]
