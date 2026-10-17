from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from django.contrib.auth import get_user_model

from students.models import StudentProfile

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        })
    )


class StudentRegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    student_id = forms.CharField(
        label='Learner Reference Number (LRN)',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'LRN'}),
        required=True,
    )
    section = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Section'}),
        required=True,
    )
    strand = forms.ChoiceField(
        choices=StudentProfile.STRAND_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id', '').strip()
        if not student_id:
            raise forms.ValidationError('LRN is required.')
        if not student_id.isdigit():
            raise forms.ValidationError('LRN must contain only digits.')
        if StudentProfile.objects.filter(student_id=student_id).exists():
            raise forms.ValidationError('A student with this LRN already exists.')
        return student_id

    def clean_section(self):
        section = self.cleaned_data.get('section', '').strip()
        if not section:
            raise forms.ValidationError('Section is required.')
        return section

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        user.is_active = True
        user.is_approved = False
        if commit:
            user.save()
        return user


class SupervisorCreateForm(UserCreationForm):
    """Only Dean can use this form to create supervisor accounts."""
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    strand = forms.ChoiceField(
        choices=StudentProfile.STRAND_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'supervisor'
        user.is_approved = True
        if commit:
            user.save()
        return user


class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )
