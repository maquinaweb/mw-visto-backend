from drf_writable_nested.serializers import WritableNestedModelSerializer
from shared_auth.serializers import OrganizationCreateSerializerMixin

from inspection.models.inspector import Inspector
from message.serializers.contact import ContactSerializer


class InspectorSerializer(
    OrganizationCreateSerializerMixin, WritableNestedModelSerializer
):
    contact = ContactSerializer()

    class Meta:
        model = Inspector
        fields = ("id", "contact")
