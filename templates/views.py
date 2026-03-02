from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Template
from .serializers import TemplateSerializer


class TemplateViewSet(viewsets.ModelViewSet):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(org=self.request.user.org)

    def get_queryset(self):
        return Template.objects.filter(org=self.request.user.org)
