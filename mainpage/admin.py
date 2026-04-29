from django.contrib import admin

from .models import (
    Announcement,
    BlockedUser,
    Club,
    Comment,
    Event,
    Like,
    Message,
    Notification,
    Post,
    Share,
    Student,
    UserWarning,
)


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'admin', 'member_count', 'created_at')
    search_fields = ('name', 'admin__username', 'admin__email')
    readonly_fields = ('created_at',)

    def member_count(self, obj):
        return obj.students.count()

    member_count.short_description = 'Registered students'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'club', 'department', 'age', 'joined_at')
    list_filter = ('club', 'department', 'joined_at')
    search_fields = ('name', 'email', 'user__username', 'club__name')
    autocomplete_fields = ('club', 'user')
    readonly_fields = ('joined_at',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'club', 'created_at')
    list_filter = ('club', 'created_at')
    search_fields = ('title', 'content', 'student__name', 'club__name')
    readonly_fields = ('created_at',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'club', 'event_type', 'event_date', 'created_by')
    list_filter = ('club', 'event_type', 'event_date')
    search_fields = ('title', 'description', 'club__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'club', 'is_important', 'created_by', 'created_at')
    list_filter = ('club', 'is_important', 'created_at')
    search_fields = ('title', 'content', 'club__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'student__name')
    readonly_fields = ('created_at',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'is_read', 'contains_warning', 'created_at')
    list_filter = ('is_read', 'contains_warning', 'created_at')
    search_fields = ('sender__name', 'recipient__name', 'content')
    readonly_fields = ('created_at',)


@admin.register(UserWarning)
class UserWarningAdmin(admin.ModelAdmin):
    list_display = ('student', 'warning_count', 'created_at')
    list_filter = ('warning_count', 'created_at')
    search_fields = ('student__name', 'reason')
    readonly_fields = ('created_at',)


@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ('blocked_by', 'blocked_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('blocked_by__name', 'blocked_user__name', 'reason')
    readonly_fields = ('created_at',)


admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Share)
