from rest_framework import serializers
from .models import Assessment

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = "__all__"
        read_only_fields = ("org", "status")

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["org"] = request.user.org
        return super().create(validated_data)
