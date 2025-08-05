from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class CustomAdminSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith('/admin/') and not hasattr(request, 'session'):
            request.session = None
            request.session_cookie_name = settings.SESSION_COOKIE_NAME_ADMIN