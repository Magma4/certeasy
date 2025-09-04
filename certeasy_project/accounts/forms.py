from django import forms
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
        'placeholder': 'Password'
    }))
