from rest_framework import serializers
from .models import Template


class TemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Template
        fields = ["id", "name", "description"]
        read_only_fields = ["id"]
