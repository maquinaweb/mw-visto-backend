from rest_framework import serializers

from inspection.models.step import InspectionStep


class InspectionStepSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="type_step.title", read_only=True)
    description = serializers.CharField(
        source="type_step.description", read_only=True
    )
    instructions = serializers.CharField(
        source="type_step.instructions", read_only=True
    )
    is_sequential = serializers.BooleanField(
        source="type_step.is_sequential", read_only=True
    )
    allow_attachment = serializers.BooleanField(
        source="type_step.allow_attachment", read_only=True
    )
    high_resolution = serializers.CharField(
        source="type_step.high_resolution", read_only=True
    )
    instruction_image = serializers.ImageField(
        source="type_step.instruction_image", read_only=True
    )

    class Meta:
        model = InspectionStep
        fields = [
            "id",
            "inspection",
            "type_step",
            "status",
            "title",
            "description",
            "instructions",
            "is_sequential",
            "allow_attachment",
            "high_resolution",
            "instruction_image",
            "order",
            "file",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
