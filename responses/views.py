from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response as DRFResponse
from django.utils import timezone

from .models import Response
from .serializers import ResponseSerializer


class ResponseViewSet(ModelViewSet):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer

    # Save draft = normal create/update already works

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        obj = self.get_object()
        # return 409 if this response is already submitted
        if getattr(obj, "submitted", False):
            return DRFResponse({"error": "Already submitted"}, status=409)

        obj.submitted = True
        obj.save()

        return DRFResponse({"message": "Submitted successfully"})
