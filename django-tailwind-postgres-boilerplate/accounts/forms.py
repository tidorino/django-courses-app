from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignupForm(UserCreationForm):
    ROLE_CHOICES = (
        ("student", "Student — I want to take courses"),
        ("instructor", "Instructor — I want to create courses"),
    )

    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect, initial="student")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "role"]
