from django.http import HttpResponse
from django.shortcuts import redirect,render

# THIS IS USED TO CREATE PERMISSIONS FOR THE GROUP AND ADMIN (WIP)

def unathenticated_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect ('admin_login')
        else:
            return view_func(request, *args, **kwargs)
    
    return wrapper_func


def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            group = None
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name

            if group in allowed_roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                return render(request, 'Errors/403.html', {'message': 'You are not authorized to view this page.'}, status=403)
        return wrapper_func
    return decorator
