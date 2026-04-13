from django.http import FileResponse
from django.views import View
from pathlib import Path


class CustomSwaggerUIView(View):
    """Custom Swagger UI view that serves a clean HTML template."""
    
    def get(self, request):
        template_path = Path(__file__).parent.parent / 'templates' / 'swagger_ui.html'
        return FileResponse(open(template_path, 'rb'), content_type='text/html')
