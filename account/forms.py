from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.apps import apps

Student = apps.get_model('account', 'Student')
Teacher = apps.get_model('account', 'Teacher')


class StudentCreationForm(UserCreationForm):
    class Meta:
        model = Student
        fields = ['username', 'first_name', 'last_name', 'email', 'contact', 'dob', 'gender', 'profile_picture']

        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter username', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Enter first name', 'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Enter last name', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter email', 'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'placeholder': 'Enter contact number', 'class': 'form-control'}),
            'dob': forms.DateInput(attrs={'placeholder': 'Select date of birth', 'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(choices=Student._meta.get_field('gender').choices, attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        student = super().save(commit=False)
        if commit:
            student.save()
        return student


class TeacherCreationForm(UserCreationForm):
    class Meta:
        model = Teacher
        fields = ['username', 'first_name', 'last_name', 'email', 'contact', 'dob', 'gender', 'category', 'profile_picture']

        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter username', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Enter first name', 'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Enter last name', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter email', 'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'placeholder': 'Enter contact number', 'class': 'form-control'}),
            'dob': forms.DateInput(attrs={'placeholder': 'Select date of birth', 'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(choices=Teacher._meta.get_field('gender').choices, attrs={'class': 'form-control'}),
            'category': forms.Select(choices=Teacher._meta.get_field('category').choices, attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        teacher = super().save(commit=False)
        if commit:
            teacher.save()
        return teacher

from django import forms
from .models import CustomUser

class UserProfileForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    dob = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    gender = forms.ChoiceField(
        choices=[('male', 'Male'), ('female', 'Female'), ('others', 'Others')],
        required=False,
    )
    contact = forms.CharField(max_length=15, required=False)
    profile_picture = forms.ImageField(required=False)

class PasswordResetEmailForm(forms.Form):
    email = forms.EmailField(label='Enter your Registered Email')