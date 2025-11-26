from django import forms
from django.forms.widgets import PasswordInput, TextInput
from django.contrib.auth import authenticate

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=TextInput(attrs={
            'class': 'login-input',
            'placeholder': 'Имя пользователя',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        max_length=120,
        widget=PasswordInput(attrs={
            'class': 'login-input',
            'placeholder': 'Пароль',
            'autocomplete': 'current-password'
        }),
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            self.user = authenticate(username=username, password=password)
            if self.user is None:
                raise forms.ValidationError('Неверное имя пользователя или пароль')           

        return cleaned_data
        