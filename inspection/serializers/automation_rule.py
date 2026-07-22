from rest_framework import serializers
from shared_auth.serializers import OrganizationCreateSerializerMixin

from inspection.models.automation_rule import AutomationRule
from inspection.serializers.inspection_motive import InspectionMotiveSerializer
from inspection.serializers.inspection_type import InspectionTypeSerializer


class AutomationRuleSerializer(OrganizationCreateSerializerMixin):
    provider_display = serializers.CharField(
        source="get_provider_display", read_only=True
    )
    event_display = serializers.CharField(
        source="get_event_display", read_only=True
    )
    inspection_type_detail = InspectionTypeSerializer(
        source="inspection_type", read_only=True
    )
    inspection_motive_detail = InspectionMotiveSerializer(
        source="inspection_motive", read_only=True
    )

    class Meta:
        model = AutomationRule
        fields = [
            "id",
            "organization_id",
            "name",
            "provider",
            "provider_display",
            "is_active",
            "event",
            "event_display",
            "inspection_type",
            "inspection_type_detail",
            "inspection_motive",
            "inspection_motive_detail",
            "target_situation_code",
            "observation_template",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization_id", "created_at", "updated_at"]
