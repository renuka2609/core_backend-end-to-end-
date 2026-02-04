from rest_framework import serializers
from .models import Remediation

class RemediationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Remediation
        fields = "__all__"
