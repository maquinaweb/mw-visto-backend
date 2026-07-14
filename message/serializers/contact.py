from drf_writable_nested.serializers import WritableNestedModelSerializer
from shared_auth.serializers import OrganizationCreateSerializerMixin
from message.models.contact import Contact
from sga.serializers.associate import AssociateSerializer


class ContactSerializer(
    WritableNestedModelSerializer, OrganizationCreateSerializerMixin
):
    associate = AssociateSerializer(required=False, allow_null=True)

    class Meta:
        model = Contact
        fields = ["id", "name", "email", "phone", "associate", "document"]
