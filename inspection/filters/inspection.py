from django_filters import rest_framework as filters

from core.filters.filter_in import CharInFilter
from inspection.models.inspection import Inspection


class InspectionFilter(filters.FilterSet):
    status = CharInFilter(field_name="status")
    created_at = filters.DateFromToRangeFilter(field_name="created_at")

    class Meta:
        model = Inspection
        fields = ["status", "created_at"]
