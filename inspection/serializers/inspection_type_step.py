from rest_framework import serializers

from inspection.models.inspection_type_step import InspectionTypeStep
from inspection.serializers.fields import PresignedFileField


class InspectionTypeStepSerializer(serializers.ModelSerializer):
    instruction_image = PresignedFileField(required=False, allow_null=True)

    class Meta:
        model = InspectionTypeStep
        fields = [
            "id",
            "inspection_type",
            "title",
            "description",
            "instructions",
            "order",
            "instruction_image",
            "is_sequential",
            "allow_attachment",
            "high_resolution",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "inspection_type", "created_at", "updated_at"]
