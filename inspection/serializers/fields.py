from urllib.parse import urlparse

from django.conf import settings
from rest_framework import serializers
from rest_framework.fields import empty


class PresignedFileField(serializers.CharField):
    def __init__(self, path_prefix=None, **kwargs):
        self.path_prefix = path_prefix
        kwargs.setdefault("allow_blank", True)
        kwargs.setdefault("allow_null", True)
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def to_representation(self, value):
        if not value or value == empty:
            return None
        if hasattr(value, "url"):
            return value.url
        return str(value)

    def to_internal_value(self, data):
        if not data:
            return "" if self.allow_blank else None

        if isinstance(data, str):
            if (
                data.startswith("http://")
                or data.startswith("https://")
                or data.startswith("/")
            ):
                parsed_url = urlparse(data)
                path = parsed_url.path.lstrip("/")

                # Strip media location prefix
                media_location = getattr(
                    settings, "PUBLIC_MEDIA_LOCATION", "media"
                )
                if path.startswith(media_location + "/"):
                    path = path[len(media_location) + 1 :]
                elif path.startswith("media/"):
                    path = path[len("media/") :]
                return path
            return data

        return super().to_internal_value(data)
