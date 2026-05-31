"""
URL configuration for studentclub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from mainpage.api_views import (
    api_admin_summary,
    api_login,
    api_me,
    api_member_profile,
    api_refresh,
    api_register,
    get_college_clubs,
)
from mainpage.views import (
    account_logout,
    admin_login,
    admin_signup,
    college_register,
    college_register_verify,
    college_login,
    college_dashboard,
    college_clubs,
    club_dashboard,
    create_post,
    delete_event,
    delete_post,
    index,
    public_college_detail,
    public_colleges,
    remove_student,
    rsvp_event,
    student_home,
    student_login,
    student_signup,
    toggle_like,
    update_event,
    add_comment,
    delete_comment,
    share_post,
    create_event,
    create_announcement,
    view_notifications,
    mark_notification_read,
    view_events,
    view_announcements,
    view_conversations,
    message_thread,
    send_message,
    get_available_users,
    block_user,
    unblock_user,
    view_user_warnings,
    forgot_password,
    password_reset_verify,
    password_reset_confirm,
    admin_edit_student_password,
    live_stats,
)

urlpatterns = [
    # Custom admin routes (must come before Django admin)
    path('admin/students/<int:student_id>/edit-password/', admin_edit_student_password, name='admin_edit_student_password'),
    
    # Django admin (catches remaining /admin/* requests)
    path('admin/', admin.site.urls),
    
    # Main app routes
    path('', index, name='home'),
    path('live-stats/', live_stats, name='live_stats'),
    path('colleges/', public_colleges, name='public_colleges'),
    path('colleges/<int:college_id>/', public_college_detail, name='public_college_detail'),
    
    # College Routes
    path('college-register/', college_register, name='college_register'),
    path('college-register/verify/', college_register_verify, name='college_register_verify'),
    path('college-login/', college_login, name='college_login'),
    path('college-dashboard/', college_dashboard, name='college_dashboard'),
    path('college/clubs/', college_clubs, name='college_clubs'),
    
    # Club Admin Routes
    path('admin-login/', admin_login, name='admin_login'),
    path('admin-signup/', admin_signup, name='admin_signup'),
    path('dashboard/', club_dashboard, name='club_dashboard'),
    
    # Student Routes
    path('student-login/', student_login, name='student_login'),
    path('student-signup/', student_signup, name='student_signup'),
    path('student-home/', student_home, name='student_home'),
    path('students/<int:student_id>/remove/', remove_student, name='remove_student'),
    
    # Post Routes
    path('posts/new/', create_post, name='create_post'),
    path('posts/<int:post_id>/like/', toggle_like, name='toggle_like'),
    path('posts/<int:post_id>/comment/', add_comment, name='add_comment'),
    path('posts/<int:post_id>/delete/', delete_post, name='delete_post'),
    path('comments/<int:comment_id>/delete/', delete_comment, name='delete_comment'),
    path('posts/<int:post_id>/share/', share_post, name='share_post'),
    
    # Event Routes
    path('events/new/', create_event, name='create_event'),
    path('events/<int:event_id>/edit/', update_event, name='update_event'),
    path('events/<int:event_id>/delete/', delete_event, name='delete_event'),
    path('events/<int:event_id>/rsvp/', rsvp_event, name='rsvp_event'),
    path('events/', view_events, name='view_events'),
    
    # Announcement Routes
    path('announcements/new/', create_announcement, name='create_announcement'),
    path('announcements/', view_announcements, name='view_announcements'),
    
    # Notification Routes
    path('notifications/', view_notifications, name='view_notifications'),
    path('notifications/<int:notification_id>/read/', mark_notification_read, name='mark_notification_read'),
    
    # Message Routes
    path('messages/conversations/', view_conversations, name='view_conversations'),
    path('messages/<int:recipient_id>/', message_thread, name='message_thread'),
    path('messages/<int:recipient_id>/send/', send_message, name='send_message'),
    path('messages/available-users/', get_available_users, name='get_available_users'),
    
    # User Routes
    path('users/<int:user_id>/block/', block_user, name='block_user'),
    path('users/<int:user_id>/unblock/', unblock_user, name='unblock_user'),
    path('warnings/', view_user_warnings, name='view_user_warnings'),
    
    # Password Reset URLs
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('password-reset/<str:token>/', password_reset_verify, name='password_reset_verify'),
    path('password-reset/<str:token>/<str:step>/', password_reset_confirm, name='password_reset_confirm'),
    
    path('logout/', account_logout, name='logout'),

    # JWT Authentication API
    path('api/auth/register/', api_register, name='api_register'),
    path('api/auth/login/', api_login, name='api_login'),
    path('api/auth/refresh/', api_refresh, name='api_refresh'),
    path('api/auth/me/', api_me, name='api_me'),
    path('api/admin/summary/', api_admin_summary, name='api_admin_summary'),
    path('api/member/profile/', api_member_profile, name='api_member_profile'),
    path('api/college-clubs/<int:college_id>/', get_college_clubs, name='get_college_clubs'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
