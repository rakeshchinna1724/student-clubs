from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import Club, Post, Student, Comment, Share, Event, Announcement, Message, PasswordReset, College
from .validators import (
    ALLOWED_SHARED_ATTACHMENT_EXTENSIONS,
    MAX_SHARED_ATTACHMENT_SIZE_MB,
)


INPUT_CLASS = 'form-input'


class CollegeRegistrationForm(UserCreationForm):
    """Form for college registration"""
    college_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS, 
            'placeholder': 'College Name',
            'autofocus': True
        }),
    )
    college_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS, 
            'placeholder': 'College Email',
        }),
    )
    admin_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS, 
            'placeholder': 'Admin Name',
        }),
    )
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS, 
            'placeholder': 'Contact Number',
        }),
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': INPUT_CLASS, 
            'placeholder': 'College Address',
            'rows': 3,
        }),
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS, 
            'placeholder': 'City',
        }),
    )
    state = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS, 
            'placeholder': 'State',
        }),
    )
    pincode = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS, 
            'placeholder': 'Pincode',
        }),
    )
    registration_number = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS, 
            'placeholder': 'College Registration Number',
        }),
    )
    
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': INPUT_CLASS, 
                'placeholder': 'Admin Username',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': INPUT_CLASS, 
            'placeholder': 'Create a password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': INPUT_CLASS, 
            'placeholder': 'Confirm password'
        })

    def clean_college_name(self):
        college_name = self.cleaned_data.get('college_name', '').strip()
        if College.objects.filter(name__iexact=college_name).exists():
            raise forms.ValidationError('This college is already registered.')
        return college_name

    def clean_college_email(self):
        college_email = self.cleaned_data.get('college_email', '').strip()
        if College.objects.filter(email__iexact=college_email).exists():
            raise forms.ValidationError('This email is already registered with another college.')
        return college_email

    def clean_registration_number(self):
        reg_no = self.cleaned_data.get('registration_number', '').strip()
        if College.objects.filter(registration_number__iexact=reg_no).exists():
            raise forms.ValidationError('This registration number is already registered.')
        return reg_no


class CollegeLoginForm(AuthenticationForm):
    """Form for college login"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS, 
            'placeholder': 'Admin Username', 
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS, 
            'placeholder': 'Password'
        })
    )


class CollegeOTPForm(forms.Form):
    """Form for verifying college registration OTP"""
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Enter 6-digit OTP',
            'autofocus': True,
            'maxlength': 6,
        }),
    )


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
        self.college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': INPUT_CLASS, 'placeholder': 'Create a password'})
        self.fields['password2'].widget.attrs.update({'class': INPUT_CLASS, 'placeholder': 'Confirm password'})

    def clean_club_name(self):
        club_name = self.cleaned_data['club_name'].strip()
        clubs = Club.objects.filter(name__iexact=club_name)
        if self.college is not None:
            clubs = clubs.filter(college=self.college)
        if clubs.exists():
            raise forms.ValidationError('This club already has an admin account.')
        return club_name


class StudentAccountForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Student username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Create a password'})
    )
    college = forms.ModelChoiceField(
        queryset=College.objects.order_by('name'),
        empty_label='Select your college',
        widget=forms.Select(attrs={'class': INPUT_CLASS})
    )
    club = forms.ModelChoiceField(
        queryset=Club.objects.order_by('name'),
        empty_label='Select your club',
        widget=forms.Select(attrs={'class': INPUT_CLASS})
    )

    class Meta:
        model = Student
        fields = ['name', 'email', 'age', 'department', 'college', 'club']
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

    def clean_password(self):
        password = self.cleaned_data['password']
        validate_password(password, user=User(username=self.cleaned_data.get('username'), email=self.cleaned_data.get('email')))
        return password

    def clean(self):
        cleaned_data = super().clean()
        college = cleaned_data.get('college')
        club = cleaned_data.get('club')
        if college and club and club.college != college:
            raise forms.ValidationError('The selected club does not belong to the selected college.')
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Start with no clubs - user must select college first
        if 'college' in self.data and self.data['college']:
            try:
                college_id = int(self.data['college'])
                self.fields['club'].queryset = Club.objects.filter(college_id=college_id).order_by('name')
            except (ValueError, TypeError):
                self.fields['club'].queryset = Club.objects.none()
        else:
            # Show no clubs until a college is selected
            self.fields['club'].queryset = Club.objects.none()


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
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
        widget=forms.DateTimeInput(attrs={
            'class': INPUT_CLASS,
            'type': 'datetime-local',
        }, format='%Y-%m-%dT%H:%M')
    )
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_type', 'location', 'event_date', 'attachment']
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
                'placeholder': 'Event location'
            }),
            'attachment': forms.FileInput(attrs={
                'class': INPUT_CLASS,
                'accept': ','.join(sorted(ALLOWED_SHARED_ATTACHMENT_EXTENSIONS)),
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.event_date:
            self.initial['event_date'] = self.instance.event_date.strftime('%Y-%m-%dT%H:%M')


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
    content = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Type your message here...',
            'rows': 3
        }),
    )

    class Meta:
        model = Message
        fields = ['content', 'attachment']
        widgets = {
            'attachment': forms.FileInput(attrs={
                'class': INPUT_CLASS,
                'accept': ','.join(sorted(ALLOWED_SHARED_ATTACHMENT_EXTENSIONS)),
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        content = (cleaned_data.get('content') or '').strip()
        attachment = cleaned_data.get('attachment')
        if not content and not attachment:
            raise forms.ValidationError('Add a message or attach a file before sending.')
        return cleaned_data


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
            validate_password(password1, user=getattr(self, 'user', None))
        
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
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_new_password(self):
        password = self.cleaned_data['new_password']
        validate_password(password, user=self.user)
        return password
