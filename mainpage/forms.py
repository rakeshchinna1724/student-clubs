from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Club, Post, Student, Comment, Share, Event, Announcement, Message, PasswordReset


INPUT_CLASS = 'form-input'


class StyledAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Username', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Password'})
    )


class ClubAdminRegistrationForm(UserCreationForm):
    club_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Club name'}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'admin@example.com'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'club_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Admin username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': INPUT_CLASS, 'placeholder': 'Create a password'})
        self.fields['password2'].widget.attrs.update({'class': INPUT_CLASS, 'placeholder': 'Confirm password'})

    def clean_club_name(self):
        club_name = self.cleaned_data['club_name'].strip()
        if Club.objects.filter(name__iexact=club_name).exists():
            raise forms.ValidationError('This club already has an admin account.')
        return club_name


class StudentAccountForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Student username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Create a password'})
    )
    club = forms.ModelChoiceField(
        queryset=Club.objects.order_by('name'),
        empty_label='Select your club',
        widget=forms.Select(attrs={'class': INPUT_CLASS})
    )

    class Meta:
        model = Student
        fields = ['name', 'email', 'age', 'department', 'club']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Full name'}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'student@example.com'}),
            'age': forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Age'}),
            'department': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Department'}),
        }

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'image', 'video']
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Post title (optional)'}),
            'content': forms.Textarea(attrs={'class': INPUT_CLASS, 'placeholder': 'Write your club post', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': INPUT_CLASS, 'accept': 'image/*'}),
            'video': forms.FileInput(attrs={'class': INPUT_CLASS, 'accept': 'video/*'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': INPUT_CLASS, 
                'placeholder': 'Write a comment...', 
                'rows': 2
            }),
        }


class ShareForm(forms.ModelForm):
    class Meta:
        model = Share
        fields = ['shared_with_message']
        widgets = {
            'shared_with_message': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Add a message (optional)',
                'rows': 2
            }),
        }


class EventForm(forms.ModelForm):
    event_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': INPUT_CLASS,
            'type': 'datetime-local',
        })
    )
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_type', 'location', 'event_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Event title'
            }),
            'description': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Event description',
                'rows': 5
            }),
            'event_type': forms.Select(attrs={
                'class': INPUT_CLASS
            }),
            'location': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Event location (optional)'
            }),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'is_important']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Announcement title'
            }),
            'content': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Write your announcement here',
                'rows': 6
            }),
            'is_important': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Type your message here...',
                'rows': 3
            }),
        }


class ForgotPasswordForm(forms.Form):
    """Form for initiating password reset process"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Enter your email address',
            'autofocus': True
        })
    )


class PasswordResetOTPForm(forms.Form):
    """Form for verifying OTP during password reset"""
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Enter 6-digit OTP',
            'autofocus': True,
            'maxlength': 6
        })
    )


class PasswordResetForm(forms.Form):
    """Form for setting new password"""
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'New password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Confirm password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password')
        password2 = cleaned_data.get('confirm_password')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('Passwords do not match!')
        
        return cleaned_data


class AdminPasswordEditForm(forms.ModelForm):
    """Form for admin to edit student password"""
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'New password'
        }),
        label='New Password'
    )
    
    class Meta:
        model = User
        fields = []
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add new_password to the form even though it's not a User field
        self.fields.move_to_end('new_password', last=False)
