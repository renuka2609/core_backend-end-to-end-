from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Vendor


class VendorSerializer(serializers.ModelSerializer):
    primary_contact_email = serializers.EmailField(source="email", allow_null=True, required=False)
    initial_risk_tier = serializers.CharField(source="tier", allow_blank=True, required=False)

    class Meta:
        model = Vendor
        fields = [
            "id",
            "org",
            "name",
            "primary_contact_email",
            "industry",
            "initial_risk_tier",
            "status",
        ]
        read_only_fields = ["id", "org"]

    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not hasattr(request, "user") or not hasattr(request.user, "org"):
            raise ValidationError({"org": "Authenticated user must belong to an organization."})

        # Ensure org is taken from the authenticated user's tenant context
        validated_data["org"] = request.user.org
        return super().create(validated_data)
