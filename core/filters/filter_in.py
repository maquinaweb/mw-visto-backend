from django_filters.filters import BaseInFilter, CharFilter, NumberFilter


class NumberInFilter(BaseInFilter, NumberFilter):
    pass


class CharInFilter(BaseInFilter, CharFilter):
    pass
