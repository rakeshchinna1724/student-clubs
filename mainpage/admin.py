from django.contrib import admin

from .models import (
    Announcement,
    BlockedUser,
    Club,
    College,
    CollegeAdmin,
    Comment,
    Event,
    EventRSVP,
    Like,
    Message,
    Notification,
    Post,
    Share,
    Student,
    UserWarning,
)


@admin.register(College)
class CollegeModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'city')
    search_fields = ('name', 'email', 'admin_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CollegeAdmin)
class CollegeAdminModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'college', 'created_at')
    list_filter = ('created_at', 'college')
    search_fields = ('user__username', 'college__name')
    readonly_fields = ('created_at',)


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
    list_display = ('name', 'email', 'club')
    search_fields = ('name', 'email', 'user__username')
    readonly_fields = ('joined_at',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'club', 'created_at')
    list_filter = ('club', 'created_at')
    search_fields = ('title', 'content', 'student__name', 'club__name')
    readonly_fields = ('created_at',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'club', 'event_type', 'event_date', 'created_by', 'has_attachment', 'rsvp_count')
    list_filter = ('club', 'event_type', 'event_date')
    search_fields = ('title', 'description', 'club__name')
    readonly_fields = ('created_at', 'updated_at')

    def rsvp_count(self, obj):
        return obj.rsvps.count()

    rsvp_count.short_description = 'RSVPs'

    def has_attachment(self, obj):
        return bool(obj.attachment)

    has_attachment.boolean = True
    has_attachment.short_description = 'Attachment'


@admin.register(EventRSVP)
class EventRSVPAdmin(admin.ModelAdmin):
    list_display = ('event', 'student', 'response', 'updated_at')
    list_filter = ('response', 'event__club', 'updated_at')
    search_fields = ('event__title', 'student__name', 'student__email')
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
    list_display = ('sender', 'recipient', 'is_read', 'contains_warning', 'has_attachment', 'created_at')
    list_filter = ('is_read', 'contains_warning', 'created_at')
    search_fields = ('sender__name', 'recipient__name', 'content')
    readonly_fields = ('created_at',)

    def has_attachment(self, obj):
        return bool(obj.attachment)

    has_attachment.boolean = True
    has_attachment.short_description = 'Attachment'


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
