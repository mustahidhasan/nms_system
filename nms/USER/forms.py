from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="First Name", max_length=30)
    last_name = forms.CharField(label="Last Name", max_length=30)
    email = forms.EmailField(label="Email", max_length=255)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "password1", "password2"]


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email", max_length=255)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
