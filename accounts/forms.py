from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('display_name', 'bio', 'avatar')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'maxlength': 280}),
            'avatar': forms.ClearableFileInput(attrs={'accept': 'image/png,image/jpeg,image/webp,image/gif'}),
        }
