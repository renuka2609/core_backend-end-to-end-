from rest_framework import serializers
from .models import Vendor


class VendorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vendor
        fields = ["id", "name"]   
        read_only_fields = ["id"]
