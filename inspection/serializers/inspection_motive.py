from rest_framework import serializers
from shared_auth.serializers import OrganizationUserCreateSerializerMixin

from inspection.models.inspection_motive import InspectionMotive


class InspectionMotiveSerializer(
    OrganizationUserCreateSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = InspectionMotive
        fields = [
            "id",
            "name",
            "description",
            "expiration_days",
            "expiration_hours",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
