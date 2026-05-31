import os

from django.db import models
from django.contrib.auth.models import User

from .validators import validate_shared_attachment


class College(models.Model):
    """College model for managing college-wise access control"""
    name = models.CharField(max_length=200, unique=True)
    email = models.EmailField(unique=True)
    admin_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    registration_number = models.CharField(max_length=100, unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CollegeAdmin(models.Model):
    """College Admin users - handles college login"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='college_admin')
    college = models.OneToOneField(College, on_delete=models.CASCADE, related_name='admin')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.college.name}"


class Club(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='clubs', null=True, blank=True)
    name = models.CharField(max_length=150)
    admin = models.OneToOneField(User, on_delete=models.CASCADE, related_name='managed_club')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('college', 'name')

    def __str__(self):
        return self.name


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='students', null=True, blank=True)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='students', null=True, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    age = models.IntegerField()
    department = models.CharField(max_length=100)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='posts')
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=180, blank=True, null=True)
    content = models.TextField()
    image = models.ImageField(upload_to='posts/images/', blank=True, null=True)
    video = models.FileField(upload_to='posts/videos/', blank=True, null=True, help_text='Supported formats: MP4, WebM, Ogg')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Post by {self.student.name}"

    class Meta:
        ordering = ['-created_at']


class Like(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'post')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.name} liked {self.post.title}"


class Comment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.student.name} commented on {self.post.title}"


class Share(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='shares')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='shares')
    shared_with_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'post')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.name} shared {self.post.title}"


class Event(models.Model):
    EVENT_TYPES = [
        ('meeting', 'Meeting'),
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
        ('social', 'Social Event'),
        ('competition', 'Competition'),
        ('other', 'Other'),
    ]
    
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='events')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='other')
    location = models.CharField(max_length=300, blank=True)
    event_date = models.DateTimeField()
    attachment = models.FileField(
        upload_to='events/files/',
        blank=True,
        null=True,
        validators=[validate_shared_attachment],
        help_text='Optional file attachment. Max 10 MB.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-event_date']
    
    def __str__(self):
        return f"{self.title} - {self.event_date}"

    @property
    def attachment_name(self):
        return os.path.basename(self.attachment.name) if self.attachment else ''


class EventRSVP(models.Model):
    RESPONSE_YES = 'yes'
    RESPONSE_NO = 'no'
    RESPONSE_CHOICES = [
        (RESPONSE_YES, 'Yes'),
        (RESPONSE_NO, 'No'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='event_rsvps')
    response = models.CharField(max_length=3, choices=RESPONSE_CHOICES)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'student')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.student.name} RSVP {self.get_response_display()} for {self.event.title}"


class Announcement(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='announcements')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_important = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('event', 'Event Created'),
        ('announcement', 'Announcement'),
        ('post_like', 'Post Liked'),
        ('post_comment', 'Post Commented'),
        ('post_share', 'Post Shared'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    related_announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    related_post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.student.name}: {self.title}"


class Message(models.Model):
    sender = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to='messages/files/',
        blank=True,
        null=True,
        validators=[validate_shared_attachment],
        help_text='Optional file attachment. Max 10 MB.',
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    contains_warning = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.sender.name} to {self.recipient.name}"

    @property
    def attachment_name(self):
        return os.path.basename(self.attachment.name) if self.attachment else ''


class UserWarning(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='warnings')
    warning_count = models.IntegerField(default=1)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Warning for {self.student.name} (Count: {self.warning_count})"


class BlockedUser(models.Model):
    blocked_by = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='blocked_users')
    blocked_user = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='blocked_by')
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('blocked_by', 'blocked_user')
    
    def __str__(self):
        return f"{self.blocked_by.name} blocked {self.blocked_user.name}"


class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=100, unique=True)
    otp = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"Password Reset for {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']
