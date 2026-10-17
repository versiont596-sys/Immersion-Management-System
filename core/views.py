from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
def redirect_view(request):
    """Redirect user to appropriate dashboard based on role."""
    user = request.user
    # Only system admin (admin user) goes to Django admin
    if user.username == 'admin' and user.is_superuser:
        return redirect('/admin/')
    elif user.role == 'dean':
        return redirect('dean:dashboard')
    elif user.role == 'supervisor':
        return redirect('supervisors:dashboard')
    elif user.role == 'student':
        return redirect('students:dashboard')
    return redirect('accounts:login')


def home_view(request):
    if request.user.is_authenticated:
        return redirect_view(request)
    return redirect('accounts:login')


def error_404(request, exception):
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    return render(request, 'errors/500.html', status=500)
