from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy
import uuid

from .forms import LoginForm, StudentRegisterForm
from .models import User
from students.models import StudentProfile


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:redirect')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_approved and user.role == 'student':
                messages.warning(
                    request,
                    'Your account is pending approval by the administrator.'
                )
                return render(request, 'accounts/login.html', {'form': form})
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('core:redirect')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('core:redirect')

    if request.method == 'POST':
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            student_profile, created = StudentProfile.objects.update_or_create(
                user=user,
                defaults={
                    'student_id': form.cleaned_data['student_id'],
                    'strand': form.cleaned_data['strand'],
                    'section': form.cleaned_data['section'],
                    'school_year': '2024-2025',
                    'application_status': 'pending',
                }
            )
            # If the profile already existed from the post_save signal, update the values.
            if not created:
                student_profile.student_id = student_profile.student_id or form.cleaned_data['student_id']
                student_profile.strand = form.cleaned_data['strand']
                student_profile.section = form.cleaned_data['section']
                student_profile.school_year = '2024-2025'
                student_profile.application_status = 'pending'
                student_profile.save()
            messages.success(
                request,
                'Your application has been submitted. Please wait for the administrator to approve your request.'
            )
            return redirect('accounts:login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentRegisterForm()

    return render(request, 'accounts/register.html', {
        'form': form,
    })


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')
