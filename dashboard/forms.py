from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'correo@ejemplo.com',
        'autocomplete': 'email'
    }))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'Nombre',
        'autocomplete': 'given-name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'Apellido',
        'autocomplete': 'family-name'
    }))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'Nombre de usuario',
        'autocomplete': 'username'
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'Contraseña',
        'autocomplete': 'new-password'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'Confirmar contraseña',
        'autocomplete': 'new-password'
    }))

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'Nombre de usuario',
        'autocomplete': 'username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'Contraseña',
        'autocomplete': 'current-password'
    }))