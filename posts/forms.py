from django import forms
from django.contrib.gis.geos import Point

from .models import Comment, Post


class PostForm(forms.ModelForm):
    latitude = forms.FloatField(required=False, widget=forms.HiddenInput())
    longitude = forms.FloatField(required=False, widget=forms.HiddenInput())
    remove_location = forms.BooleanField(required=False)

    class Meta:
        model = Post
        fields = ('content', 'image', 'location_name', 'city')
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': "What's happening?"}),
            'location_name': forms.TextInput(attrs={'placeholder': 'Add location (optional)'}),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/png,image/jpeg,image/webp,image/gif'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        lat = cleaned_data.get('latitude')
        lng = cleaned_data.get('longitude')

        if lat is not None and lng is not None:
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                raise forms.ValidationError('Invalid coordinates.')

        return cleaned_data

    def save(self, commit=True):
        post = super().save(commit=False)

        if self.cleaned_data.get('remove_location'):
            post.location = None
            post.location_name = ''
            post.city = ''
        else:
            lat = self.cleaned_data.get('latitude')
            lng = self.cleaned_data.get('longitude')
            if lat is not None and lng is not None:
                post.location = Point(lng, lat, srid=4326)

        if commit:
            post.save()
        return post


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
        widgets = {
            'content': forms.TextInput(attrs={'placeholder': 'Add a comment...'}),
        }
