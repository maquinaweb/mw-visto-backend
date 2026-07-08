from rest_framework import serializers

from inspection.models.step import InspectionStep


class InspectionStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionStep
        fields = [
            "id",
            "inspection",
            "title",
            "description",
            "instructions",
            "order",
            "photo",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
