from django import forms
from django.forms.widgets import PasswordInput, TextInput, EmailInput
from django.contrib.auth import authenticate
from core.models import Question, Tag, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class PasswordChangeForm(forms.Form):
    password1 = forms.CharField(
        max_length=120,
        widget=forms.PasswordInput(attrs={
            'class': 'settings-input',
            'placeholder': 'Новый пароль',
            'autocomplete': 'new-password',
        }),
        label='Новый пароль'
    )
    password2 = forms.CharField(
        max_length=120,
        widget=forms.PasswordInput(attrs={
            'class': 'settings-input',
            'placeholder': 'Повторите пароль',
            'autocomplete': 'new-password',
        }),
        label='Повторите пароль'
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')

        if not p1 or not p2:
            raise ValidationError('Введите пароль дважды')
        if p1 != p2:
            raise ValidationError('Пароли не совпадают')

        validate_password(p2)
        return cleaned_data

    def save(self, user, commit=True):
        password = self.cleaned_data['password1']
        user.set_password(password)
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Имя пользователя',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        max_length=120,
        widget=PasswordInput(attrs={
            'class': 'auth-input',
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
                raise ValidationError('Неверное имя пользователя или пароль')           

        return cleaned_data
        

class SignupForm(PasswordChangeForm, forms.ModelForm):   

    class Meta:
        model = User
        fields = ('username', 'email')
        widgets = {
            'username': TextInput(attrs={
                'class': 'auth-input',
                'placeholder': 'Имя пользователя',
                'autocomplete': 'username',
            }),
             'email': EmailInput(attrs={
                'class': 'auth-input',
                'placeholder': 'Email',
                'autocomplete': 'email',
            }),
        }
        labels = {
            'username': 'Имя пользователя',
            'email': 'Email',
        }          

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Пользователь с таким именем уже существует')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email
        
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data['password1']
        user.set_password(password) 
        if commit:
            user.save()
        return user


class QuestionForm(forms.Form):
    title = forms.CharField(
        label='Заголовок вопроса',
        widget=forms.TextInput(attrs={
            'class': 'form-input'
            })
    )
    detailed = forms.CharField(
        label='Описание вопроса',
        widget=forms.Textarea(attrs={
            'class': 'form-textarea'
            })
    )
    tags = forms.CharField(
        label='Теги',
        required=False,
        widget=forms.HiddenInput() 
    )


class SettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'avatar')
        widgets = {
            'username': TextInput(attrs={
                'class': 'settings-input',
                'placeholder': 'Имя пользователя',
                'autocomplete': 'username',
            }),
             'email': EmailInput(attrs={
                'class': 'settings-input',
                'placeholder': 'Email',
                'autocomplete': 'email',
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'settings-input',
            })
        }
        labels = {
            'username': 'Имя пользователя',
            'email': 'Email',
            'avatar': 'Аватар',
        }


