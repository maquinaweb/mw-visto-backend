from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Prefetch
from rest_framework import serializers, viewsets


class OptimizedModelSerializer(serializers.ModelSerializer):
    omit = ()

    def __init__(self, *args, **kwargs):
        omit = kwargs.pop("omit", None)
        super().__init__(*args, **kwargs)

        # Initialize select_related and prefetch_related sets
        self._select_related = set()
        self._prefetch_related = set()

        # Analyze fields to determine relationships
        for field_name, field in self.fields.items():
            if isinstance(
                field,
                (serializers.PrimaryKeyRelatedField),
            ):
                self.fields[field_name] = serializers.PrimaryKeyRelatedField(
                    read_only=field.read_only or True
                )
            elif isinstance(
                field,
                (serializers.ManyRelatedField),
            ):
                self.fields[field_name] = serializers.PrimaryKeyRelatedField(
                    read_only=field.read_only or True, many=True
                )

            # Check if field is a nested serializer
            if isinstance(field, serializers.ModelSerializer):
                try:
                    model_field = self.Meta.model._meta.get_field(field_name)
                    if isinstance(model_field, models.ForeignKey):
                        self._select_related.add(field_name)
                    elif isinstance(model_field, models.ManyToManyField):
                        self._prefetch_related.add(field_name)
                except FieldDoesNotExist:
                    pass

            # Check if field is a reverse relation
            elif isinstance(field, serializers.ManyRelatedField):
                try:
                    model_field = self.Meta.model._meta.get_field(field_name)
                    if isinstance(model_field, models.ManyToManyField):
                        self._prefetch_related.add(field_name)
                except FieldDoesNotExist:
                    pass

        if omit:
            for field_name in omit:
                self.fields.pop(field_name, None)

        self.omit = omit

    def get_queryset(self, queryset):
        model = queryset.model
        valid_fields = []

        # Add select_related fields
        if self._select_related:
            queryset = queryset.select_related(*self._select_related)

        # Add prefetch_related fields
        if self._prefetch_related:
            prefetch_objects = []
            for prefetch in self._prefetch_related:
                if isinstance(prefetch, tuple):
                    prefetch_objects.append(Prefetch(*prefetch))
                else:
                    prefetch_objects.append(prefetch)
            queryset = queryset.prefetch_related(*prefetch_objects)

        # Add only fields
        for field_name, field in self.fields.items():
            try:
                model._meta.get_field(field_name)
                valid_fields.append(field_name)
            except FieldDoesNotExist:
                pass

        return queryset.only(*valid_fields)


class OptimizedViewSetMixin(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.serializer_class, "get_queryset"):
            return self.serializer_class().get_queryset(queryset)
        return queryset
