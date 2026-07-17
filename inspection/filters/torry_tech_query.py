from django_filters import rest_framework as filters
from inspection.models.torry_tech_query import TorryTechQuery


class TorryTechQueryFilter(filters.FilterSet):
    inspection = filters.NumberFilter(field_name="inspection_id")

    class Meta:
        model = TorryTechQuery
        fields = ["inspection"]
