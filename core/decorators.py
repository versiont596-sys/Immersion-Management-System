from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def student_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.role != 'student':
            messages.error(request, 'Access denied. Students only.')
            return redirect('core:redirect')
        if not request.user.is_approved:
            messages.warning(request, 'Your account is pending approval.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def supervisor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.role != 'supervisor':
            messages.error(request, 'Access denied. Supervisors only.')
            return redirect('core:redirect')
        return view_func(request, *args, **kwargs)
    return wrapper


def dean_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.role not in ('dean',) and not request.user.is_superuser:
            messages.error(request, 'Access denied. Administrator only.')
            return redirect('core:redirect')
        return view_func(request, *args, **kwargs)
    return wrapper
