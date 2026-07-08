from rest_framework import filters


class IncludeExcludeFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        include_ids = self._parse_ids(request.query_params.get("include"))
        exclude_ids = self._parse_ids(request.query_params.get("exclude"))

        if exclude_ids:
            queryset = queryset.exclude(pk__in=exclude_ids)

        if include_ids:
            base_queryset = view.get_queryset()
            include_queryset = base_queryset.filter(pk__in=include_ids)
            queryset = queryset.union(include_queryset)

        return queryset

    @staticmethod
    def _parse_ids(raw_value):
        if not raw_value:
            return []
        return [
            value.strip() for value in raw_value.split(",") if value.strip()
        ]
