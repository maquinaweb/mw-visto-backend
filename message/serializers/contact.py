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

    def create(self, validated_data):
        request = self.context.get("request")
        org_id = None
        if request and hasattr(request, "organization_id"):
            org_id = request.organization_id

        if org_id is not None:
            validated_data["organization_id"] = org_id
        else:
            org_id = validated_data.get("organization_id")

        email = validated_data.get("email")
        document = validated_data.get("document")

        contact = None
        has_email = isinstance(email, str) and email.strip()
        has_document = isinstance(document, str) and document.strip()
        if has_email or has_document:
            contact = Contact.objects.filter(
                organization_id=org_id,
                email=email,
                document=document,
            ).first()

        if contact:
            return self.update(contact, validated_data)

        return super().create(validated_data)
