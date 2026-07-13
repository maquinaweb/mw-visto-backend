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
            "order",
            "file",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
