from rest_framework import serializers
from .models import Response


class ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Response
        fields = "__all__"
        read_only_fields = [
            "id",
            "submitted",
        ]

    def create(self, validated_data):
        # assessment should be provided in the payload (or set by the view)
        return super().create(validated_data)
