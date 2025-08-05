from django.shortcuts import render
from django.conf import settings

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        maintenance_on = getattr(settings, "MAINTENANCE_MODE", False)
        
        # Get user only if attribute exists
        user = getattr(request, "user", None)
        
        if maintenance_on and not (user and user.is_staff):
            return render(request, "maintenance.html", status=503)

        return self.get_response(request)
