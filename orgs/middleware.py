from django.utils.deprecation import MiddlewareMixin

class TenantMiddleware(MiddlewareMixin):
    """
    Attaches org_id to request for tenant isolation
    """

    def process_request(self, request):
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            request.org_id = getattr(user, "org_id", None)
        else:
            request.org_id = None
