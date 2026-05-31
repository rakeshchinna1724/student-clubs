from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Prefetch, Q
from django.contrib import messages as django_messages
from datetime import datetime, timedelta

from .forms import AdminPasswordEditForm, ClubAdminRegistrationForm, PostForm, StyledAuthenticationForm, StudentAccountForm, CommentForm, ShareForm, EventForm, AnnouncementForm, MessageForm, ForgotPasswordForm, PasswordResetOTPForm, PasswordResetForm, CollegeRegistrationForm, CollegeLoginForm, CollegeOTPForm
from .models import Club, Post, Student, Like, Comment, Share, Event, EventRSVP, Announcement, Notification, Message, UserWarning, BlockedUser, College, CollegeAdmin
from .utils import contains_bad_words, add_warning, should_block_user, can_message
from .password_utils import create_password_reset_request, send_password_reset_email, verify_otp_and_get_reset_request, reset_user_password, generate_otp, send_college_registration_otp_email


def build_live_stats():
    return {
        'active_members': Student.objects.count(),
        'posts_shared': Post.objects.count(),
        'clubs_count': Club.objects.count(),
        'events_count': Event.objects.count(),
        'announcements_count': Announcement.objects.count(),
        'messages_count': Message.objects.count(),
    }


def index(request):
    """Landing page - shows college registration/login if unauthenticated, college dashboard if authenticated"""
    if request.user.is_authenticated:
        return role_redirect(request.user)
    
    # Show ONLY college registration/login for unauthenticated users
    context = {
        'is_college_authenticated': False,
    }
    return render(request, 'mainpage/index.html', context)


def public_colleges(request):
    """Public page listing colleges with live club and student counts."""
    colleges = College.objects.annotate(
        club_count=Count('clubs', distinct=True),
        student_count=Count('clubs__students', distinct=True),
    ).order_by('name')

    return render(request, 'mainpage/public_colleges.html', {
        'colleges': colleges,
        'stats': {
            'colleges_count': colleges.count(),
            'clubs_count': Club.objects.count(),
            'students_count': Student.objects.count(),
        },
    })


def public_college_detail(request, college_id):
    """Public page showing clubs and members for one college."""
    college = get_object_or_404(
        College.objects.annotate(
            club_count=Count('clubs', distinct=True),
            student_count=Count('clubs__students', distinct=True),
        ),
        id=college_id,
    )
    clubs = college.clubs.select_related('admin').prefetch_related(
        Prefetch('students', queryset=Student.objects.select_related('user').order_by('name'))
    ).annotate(
        member_count=Count('students', distinct=True),
        post_count=Count('posts', distinct=True),
        event_count=Count('events', distinct=True),
    ).order_by('name')

    return render(request, 'mainpage/public_college_detail.html', {
        'college': college,
        'clubs': clubs,
    })


def role_redirect(user):
    if hasattr(user, 'college_admin'):
        return redirect('college_dashboard')
    if hasattr(user, 'managed_club'):
        return redirect('club_dashboard')
    if hasattr(user, 'student_profile'):
        return redirect('student_home')
    if user.is_staff or user.is_superuser:
        return redirect('/admin/')
    return redirect('logout')


def admin_signup(request):
    college = None
    creating_for_college = request.user.is_authenticated and hasattr(request.user, 'college_admin')
    if creating_for_college:
        college = request.user.college_admin.college
    elif request.user.is_authenticated:
        return role_redirect(request.user)
    else:
        return redirect('college_login')

    if request.method == 'POST':
        form = ClubAdminRegistrationForm(request.POST, college=college)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            Club.objects.create(name=form.cleaned_data['club_name'], admin=user, college=college)
            if creating_for_college:
                django_messages.success(request, f"{form.cleaned_data['club_name']} club created successfully.")
                return redirect('college_dashboard')
            login(request, user)
            return redirect('club_dashboard')
    else:
        form = ClubAdminRegistrationForm(college=college)

    return render(request, 'mainpage/admin_signup.html', {
        'form': form,
        'creating_for_college': creating_for_college,
        'college': college,
    })


def admin_login(request):
    if request.user.is_authenticated:
        return role_redirect(request.user)

    if request.method == 'POST':
        form = StyledAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if hasattr(user, 'managed_club'):
                login(request, user)
                return redirect('club_dashboard')
            form.add_error(None, 'This account is not a club admin account.')
    else:
        form = StyledAuthenticationForm()

    return render(request, 'mainpage/admin_login.html', {'form': form})


def college_register(request):
    """College registration page"""
    if request.user.is_authenticated:
        return role_redirect(request.user)

    if request.method == 'POST':
        form = CollegeRegistrationForm(request.POST)
        if form.is_valid():
            otp = generate_otp()
            pending_registration = {
                'college_name': form.cleaned_data['college_name'],
                'college_email': form.cleaned_data['college_email'],
                'admin_name': form.cleaned_data['admin_name'],
                'phone': form.cleaned_data['phone'],
                'address': form.cleaned_data['address'],
                'city': form.cleaned_data['city'],
                'state': form.cleaned_data['state'],
                'pincode': form.cleaned_data['pincode'],
                'registration_number': form.cleaned_data['registration_number'],
                'username': form.cleaned_data['username'],
                'password': form.cleaned_data['password1'],
                'otp': otp,
                'expires_at': (timezone.now() + timedelta(minutes=10)).isoformat(),
            }

            email_sent = send_college_registration_otp_email(
                pending_registration['college_email'],
                otp,
                pending_registration['college_name'],
            )
            if email_sent:
                request.session['pending_college_registration'] = pending_registration
                django_messages.success(request, 'OTP has been sent to the college email. Please verify to complete registration.')
                return redirect('college_register_verify')
            form.add_error('college_email', 'Could not send OTP. Please check the email settings and try again.')
    else:
        form = CollegeRegistrationForm()

    return render(request, 'mainpage/college_register.html', {'form': form})


def college_register_verify(request):
    """Verify college email OTP and create the college admin account."""
    if request.user.is_authenticated:
        return role_redirect(request.user)

    pending_registration = request.session.get('pending_college_registration')
    if not pending_registration:
        django_messages.info(request, 'Please start college registration first.')
        return redirect('college_register')

    expires_at = datetime.fromisoformat(pending_registration['expires_at'])
    if timezone.is_naive(expires_at):
        expires_at = timezone.make_aware(expires_at)
    if expires_at <= timezone.now():
        request.session.pop('pending_college_registration', None)
        django_messages.error(request, 'OTP expired. Please register again.')
        return redirect('college_register')

    if request.method == 'POST':
        form = CollegeOTPForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['otp'] != pending_registration['otp']:
                form.add_error('otp', 'Invalid OTP. Please try again.')
            elif User.objects.filter(username__iexact=pending_registration['username']).exists():
                request.session.pop('pending_college_registration', None)
                django_messages.error(request, 'This username was already taken. Please register again.')
                return redirect('college_register')
            elif College.objects.filter(name__iexact=pending_registration['college_name']).exists():
                request.session.pop('pending_college_registration', None)
                django_messages.error(request, 'This college is already registered. Please login.')
                return redirect('college_login')
            elif College.objects.filter(email__iexact=pending_registration['college_email']).exists():
                request.session.pop('pending_college_registration', None)
                django_messages.error(request, 'This college email is already registered. Please login.')
                return redirect('college_login')
            elif College.objects.filter(registration_number__iexact=pending_registration['registration_number']).exists():
                request.session.pop('pending_college_registration', None)
                django_messages.error(request, 'This registration number is already registered.')
                return redirect('college_register')
            else:
                user = User.objects.create_user(
                    username=pending_registration['username'],
                    email=pending_registration['college_email'],
                    password=pending_registration['password'],
                )
                college = College.objects.create(
                    name=pending_registration['college_name'],
                    email=pending_registration['college_email'],
                    admin_name=pending_registration['admin_name'],
                    phone=pending_registration['phone'],
                    address=pending_registration['address'],
                    city=pending_registration['city'],
                    state=pending_registration['state'],
                    pincode=pending_registration['pincode'],
                    registration_number=pending_registration['registration_number'],
                    is_verified=True,
                )
                CollegeAdmin.objects.create(user=user, college=college)
                request.session.pop('pending_college_registration', None)
                login(request, user)
                django_messages.success(request, 'College email verified and registration completed.')
                return redirect('college_dashboard')
    else:
        form = CollegeOTPForm()

    return render(request, 'mainpage/college_register_verify.html', {
        'form': form,
        'college_email': pending_registration['college_email'],
        'college_name': pending_registration['college_name'],
    })


def college_login(request):
    """College login page"""
    if request.user.is_authenticated:
        return role_redirect(request.user)

    if request.method == 'POST':
        form = CollegeLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if hasattr(user, 'college_admin'):
                login(request, user)
                django_messages.success(request, f'Welcome back to {user.college_admin.college.name}!')
                return redirect('college_dashboard')
            form.add_error(None, 'This account is not a college admin account.')
    else:
        form = CollegeLoginForm()

    return render(request, 'mainpage/college_login.html', {'form': form})


@login_required(login_url='college_login')
def college_dashboard(request):
    """College admin dashboard"""
    if not hasattr(request.user, 'college_admin'):
        return redirect('college_login')
    
    college = request.user.college_admin.college
    clubs = college.clubs.all().annotate(
        member_count=Count('students', distinct=True),
        post_count=Count('posts', distinct=True),
        event_count=Count('events', distinct=True),
    )
    
    stats = {
        'total_clubs': clubs.count(),
        'total_students': Student.objects.filter(club__college=college).count(),
        'total_posts': Post.objects.filter(club__college=college).count(),
        'total_events': Event.objects.filter(club__college=college).count(),
        'total_announcements': Announcement.objects.filter(club__college=college).count(),
    }
    
    return render(request, 'mainpage/college_dashboard.html', {
        'college': college,
        'clubs': clubs,
        'stats': stats,
    })


@login_required(login_url='college_login')
def college_clubs(request):
    """View all clubs in the college"""
    if not hasattr(request.user, 'college_admin'):
        return redirect('college_login')
    
    college = request.user.college_admin.college
    clubs = college.clubs.all().annotate(
        member_count=Count('students', distinct=True),
        post_count=Count('posts', distinct=True),
        event_count=Count('events', distinct=True),
    )
    
    return render(request, 'mainpage/college_clubs.html', {
        'college': college,
        'clubs': clubs,
    })


def student_login(request):
    if request.user.is_authenticated:
        return role_redirect(request.user)

    if request.method == 'POST':
        form = StyledAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if hasattr(user, 'student_profile'):
                login(request, user)
                return redirect('student_home')
            form.add_error(None, 'This account is not a student account.')
    else:
        form = StyledAuthenticationForm()

    return render(request, 'mainpage/student_login.html', {'form': form})


def student_signup(request):
    if request.user.is_authenticated:
        return role_redirect(request.user)

    if request.method == 'POST':
        form = StudentAccountForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            student = form.save(commit=False)
            student.user = user
            student.college = form.cleaned_data['college']
            student.club = form.cleaned_data['club']
            student.save()
            login(request, user)
            return redirect('student_home')
    else:
        form = StudentAccountForm()

    return render(request, 'mainpage/student_signup.html', {'form': form})


@login_required(login_url='admin_login')
def club_dashboard(request):
    club = get_object_or_404(Club, admin=request.user)
    students = club.students.select_related('user').order_by('-joined_at')
    posts = club.posts.select_related('student', 'student__user').prefetch_related('likes', 'comments', 'shares').order_by('-created_at')
    dashboard_stats = {
        'members_count': students.count(),
        'posts_count': posts.count(),
        'events_count': club.events.count(),
        'announcements_count': club.announcements.count(),
        'engagement_count': Like.objects.filter(post__club=club).count() + Comment.objects.filter(post__club=club).count() + Share.objects.filter(post__club=club).count(),
    }
    recent_members = students[:6]
    recent_posts = posts[:5]
    recent_events = list(club.events.prefetch_related('rsvps').order_by('-event_date')[:5])
    for event in recent_events:
        event.yes_count = event.rsvps.filter(response=EventRSVP.RESPONSE_YES).count()
        event.no_count = event.rsvps.filter(response=EventRSVP.RESPONSE_NO).count()
    return render(request, 'mainpage/club_dashboard.html', {
        'club': club,
        'students': students,
        'posts': posts,
        'dashboard_stats': dashboard_stats,
        'recent_members': recent_members,
        'recent_posts': recent_posts,
        'recent_events': recent_events,
    })


@login_required(login_url='admin_login')
@require_POST
def remove_student(request, student_id):
    club = get_object_or_404(Club, admin=request.user)
    student = get_object_or_404(Student.objects.select_related('user'), id=student_id, club=club)
    student.user.delete()
    return redirect('club_dashboard')


@login_required(login_url='student_login')
def student_home(request):
    try:
        student = Student.objects.select_related('club', 'user').get(user=request.user)
        posts = student.club.posts.select_related('student', 'student__user').prefetch_related(
            'likes', 
            'comments__student',
            'shares'
        ).order_by('-created_at') if student.club else []
    except Student.DoesNotExist:
        django_messages.error(request, "You must have a student profile to view the home page.")
        return redirect('student_login')
    liked_post_ids = set(Like.objects.filter(student=student, post__club=student.club).values_list('post_id', flat=True)) if student.club else set()
    club_stats = {
        'posts_count': student.club.posts.count() if student.club else 0,
        'members_count': student.club.students.count() if student.club else 0,
        'events_count': student.club.events.count() if student.club else 0,
        'announcements_count': student.club.announcements.count() if student.club else 0,
    }
    return render(request, 'mainpage/student_home.html', {
        'student': student,
        'posts': posts,
        'liked_post_ids': liked_post_ids,
        'club_stats': club_stats,
    })


def live_stats(request):
    """Return homepage statistics for live refresh."""
    return JsonResponse(build_live_stats())


@login_required(login_url='student_login')
def create_post(request):
    try:
        student = Student.objects.select_related('club').get(user=request.user)
    except Student.DoesNotExist:
        django_messages.error(request, "You must have a student profile to create posts.")
        return redirect('student_home')

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.student = student
            post.club = student.club
            post.save()
            django_messages.success(request, 'Post created successfully!')
            return redirect('student_home')
        else:
            django_messages.error(request, 'Error creating post. Please check the form.')
    else:
        form = PostForm()

    return render(request, 'mainpage/create_post.html', {'form': form, 'student': student})


@login_required(login_url='student_login')
@require_POST
def toggle_like(request, post_id):
    """Toggle like on a post"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        django_messages.error(request, "You must have a student profile to like posts.")
        return redirect('student_home')
    post = get_object_or_404(Post, id=post_id, club=student.club)
    
    like, created = Like.objects.get_or_create(student=student, post=post)
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'likes_count': post.likes.count()
        })
    
    return redirect('student_home')


@login_required(login_url='student_login')
def add_comment(request, post_id):
    """Add a comment to a post"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        django_messages.error(request, "You must have a student profile to comment on posts.")
        return redirect('student_home')
    post = get_object_or_404(Post, id=post_id, club=student.club)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.student = student
            comment.post = post
            comment.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'comment_id': comment.id,
                    'student_name': student.name,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
                })
    else:
        form = CommentForm()
    
    return redirect('student_home')


@login_required(login_url='student_login')
@require_POST
def delete_comment(request, comment_id):
    """Delete a comment (only by the author or admin)"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        django_messages.error(request, "You must have a student profile to delete comments.")
        return redirect('student_home')
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.student == student:
        comment.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
    
    return redirect('student_home')


@login_required(login_url='student_login')
@require_POST
def delete_post(request, post_id):
    """Delete a post (only by the author)"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        django_messages.error(request, "You must have a student profile to delete posts.")
        return redirect('student_home')
    
    post = get_object_or_404(Post, id=post_id)
    
    if post.student == student:
        post.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        django_messages.success(request, 'Post deleted successfully!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'You cannot delete this post.'})
        django_messages.error(request, 'You cannot delete this post.')
    
    return redirect('student_home')


@login_required(login_url='student_login')
def share_post(request, post_id):
    """Share a post"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        django_messages.error(request, "You must have a student profile to share posts.")
        return redirect('student_home')
    post = get_object_or_404(Post, id=post_id, club=student.club)
    
    if request.method == 'POST':
        form = ShareForm(request.POST)
        if form.is_valid():
            share, created = Share.objects.get_or_create(
                student=student, 
                post=post,
                defaults={'shared_with_message': form.cleaned_data.get('shared_with_message', '')}
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'shares_count': post.shares.count()
                })
            
            return redirect('student_home')
    else:
        form = ShareForm()
    
    return render(request, 'mainpage/share_post.html', {'form': form, 'post': post})


@login_required(login_url='admin_login')
def create_event(request):
    """Admin creates an event"""
    club = get_object_or_404(Club, admin=request.user)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.club = club
            event.created_by = request.user
            event.save()
            
            # Create notifications for all club students
            students = club.students.all()
            for student in students:
                Notification.objects.create(
                    student=student,
                    notification_type='event',
                    title=f"New Event: {event.title}",
                    message=f"{event.title} is scheduled for {event.event_date.strftime('%B %d, %Y at %I:%M %p')}",
                    related_event=event
                )
            
            return redirect('club_dashboard')
    else:
        form = EventForm()
    
    return render(request, 'mainpage/create_event.html', {'form': form, 'club': club, 'is_edit': False})


@login_required(login_url='admin_login')
def update_event(request, event_id):
    """Admin updates an event for their club"""
    club = get_object_or_404(Club, admin=request.user)
    event = get_object_or_404(Event, id=event_id, club=club)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            django_messages.success(request, 'Event updated successfully.')
            return redirect('club_dashboard')
    else:
        form = EventForm(instance=event)

    return render(request, 'mainpage/create_event.html', {
        'form': form,
        'club': club,
        'event': event,
        'is_edit': True,
    })


@login_required(login_url='admin_login')
@require_POST
def delete_event(request, event_id):
    """Admin deletes an event for their club"""
    club = get_object_or_404(Club, admin=request.user)
    event = get_object_or_404(Event, id=event_id, club=club)
    event.delete()
    django_messages.success(request, 'Event deleted successfully.')
    return redirect('club_dashboard')


@login_required(login_url='admin_login')
def create_announcement(request):
    """Admin creates an announcement"""
    club = get_object_or_404(Club, admin=request.user)
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.club = club
            announcement.created_by = request.user
            announcement.save()
            
            # Create notifications for all club students
            students = club.students.all()
            for student in students:
                Notification.objects.create(
                    student=student,
                    notification_type='announcement',
                    title=announcement.title,
                    message=announcement.content[:100] + '...' if len(announcement.content) > 100 else announcement.content,
                    related_announcement=announcement
                )
            
            return redirect('club_dashboard')
    else:
        form = AnnouncementForm()
    
    return render(request, 'mainpage/create_announcement.html', {'form': form, 'club': club})


@login_required(login_url='student_login')
def view_notifications(request):
    """View all notifications for a student"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        django_messages.error(request, "You must have a student profile to view notifications.")
        return redirect('student_home')
    notifications = student.notifications.all()
    unread_count = notifications.filter(is_read=False).count()
    
    return render(request, 'mainpage/notifications.html', {
        'student': student,
        'notifications': notifications,
        'unread_count': unread_count
    })


@login_required(login_url='student_login')
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        django_messages.error(request, "You must have a student profile to access notifications.")
        return redirect('student_home')
    notification = get_object_or_404(Notification, id=notification_id, student=student)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('view_notifications')


@login_required(login_url='student_login')
def view_events(request):
    """View upcoming events"""
    try:
        student = Student.objects.get(user=request.user)
        events = list(student.club.events.select_related('created_by').prefetch_related('rsvps').all()) if student.club else []
    except Student.DoesNotExist:
        django_messages.error(request, "You must have a student profile to view events.")
        return redirect('student_home')

    rsvps = EventRSVP.objects.filter(student=student, event__in=events)
    rsvp_by_event_id = {rsvp.event_id: rsvp.response for rsvp in rsvps}
    for event in events:
        event.current_rsvp = rsvp_by_event_id.get(event.id)
        event.yes_count = event.rsvps.filter(response=EventRSVP.RESPONSE_YES).count()
        event.no_count = event.rsvps.filter(response=EventRSVP.RESPONSE_NO).count()
    
    return render(request, 'mainpage/view_events.html', {
        'student': student,
        'events': events
    })


@login_required(login_url='student_login')
@require_POST
def rsvp_event(request, event_id):
    """Student RSVP for an event in their club"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        django_messages.error(request, "You must have a student profile to RSVP for events.")
        return redirect('student_home')

    event = get_object_or_404(Event, id=event_id)
    if event.club_id != student.club_id:
        django_messages.error(request, 'You can only RSVP for events in your club.')
        return redirect('view_events')
    response = request.POST.get('response')
    if response not in {EventRSVP.RESPONSE_YES, EventRSVP.RESPONSE_NO}:
        django_messages.error(request, 'Please choose Yes or No for your RSVP.')
        return redirect('view_events')

    EventRSVP.objects.update_or_create(
        event=event,
        student=student,
        defaults={'response': response},
    )
    django_messages.success(request, f'Your RSVP for {event.title} was saved.')
    return redirect('view_events')


@login_required(login_url='student_login')
def view_announcements(request):
    """View club announcements"""
    try:
        student = Student.objects.get(user=request.user)
        announcements = student.club.announcements.all() if student.club else []
    except Student.DoesNotExist:
        django_messages.error(request, "You must have a student profile to view announcements.")
        return redirect('student_home')
    
    return render(request, 'mainpage/view_announcements.html', {
        'student': student,
        'announcements': announcements
    })


def account_logout(request):
    """Logout user and redirect to home page"""
    logout(request)
    return redirect('home')


@login_required(login_url='student_login')
def view_conversations(request):
    """View all conversations for a student"""
    # Get student profile safely
    if not hasattr(request.user, 'student_profile') or request.user.student_profile is None:
        django_messages.error(request, 'Only students can access messaging.')
        return redirect('student_login')
    
    student = request.user.student_profile
    
    # Get all unique students we've messaged with (sent or received)
    sent_to = Message.objects.filter(sender=student).values_list('recipient_id', flat=True).distinct()
    received_from = Message.objects.filter(recipient=student).values_list('sender_id', flat=True).distinct()
    
    conversation_ids = set(sent_to) | set(received_from)
    conversations = Student.objects.filter(id__in=conversation_ids).select_related('club', 'user')
    
    # Get latest message for each conversation
    conversation_data = []
    for conv_student in conversations:
        latest_message = Message.objects.filter(
            Q(sender=student, recipient=conv_student) | Q(sender=conv_student, recipient=student)
        ).order_by('-created_at').first()
        
        # Check if blocked
        is_blocked = BlockedUser.objects.filter(
            Q(blocked_by=student, blocked_user=conv_student) | Q(blocked_by=conv_student, blocked_user=student)
        ).exists()
        
        conversation_data.append({
            'student': conv_student,
            'latest_message': latest_message,
            'is_blocked': is_blocked
        })
    
    return render(request, 'mainpage/conversations.html', {
        'student': student,
        'conversation_data': conversation_data
    })


@login_required(login_url='student_login')
def message_thread(request, recipient_id):
    """View message thread with another student"""
    # Get student profile safely
    if not hasattr(request.user, 'student_profile') or request.user.student_profile is None:
        django_messages.error(request, 'Only students can access messaging.')
        return redirect('student_login')
    
    sender = request.user.student_profile
    recipient = get_object_or_404(Student, id=recipient_id)
    
    # Check if they are in same club or if blocked
    if sender.club != recipient.club:
        django_messages.error(request, 'You can only message members in your club.')
        return redirect('view_conversations')
    
    # Check if blocked
    is_blocked = BlockedUser.objects.filter(
        Q(blocked_by=sender, blocked_user=recipient) | Q(blocked_by=recipient, blocked_user=sender)
    ).exists()
    
    if is_blocked:
        django_messages.error(request, 'You cannot message this user - one of you has blocked the other.')
        return redirect('view_conversations')
    
    # Get all messages in conversation
    messages_list = Message.objects.filter(
        Q(sender=sender, recipient=recipient) | Q(sender=recipient, recipient=sender)
    ).order_by('created_at')
    
    # Mark unread messages as read
    messages_list.filter(recipient=sender, is_read=False).update(is_read=True)
    
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            # Check for bad words
            content = form.cleaned_data['content'].strip()
            has_bad_words = contains_bad_words(content)
            
            message = form.save(commit=False)
            message.content = content
            message.sender = sender
            message.recipient = recipient
            message.contains_warning = has_bad_words
            message.save()
            
            if has_bad_words:
                # Add warning to sender
                warning_count = add_warning(sender, f"Sent message with inappropriate content to {recipient.name}")
                
                if should_block_user(warning_count):
                    # Block the user
                    BlockedUser.objects.get_or_create(blocked_by=recipient, blocked_user=sender)
                    django_messages.warning(request, 
                        f'Your message contained inappropriate content. You received {warning_count} warnings and have been BLOCKED by this user.')
                    return redirect('view_conversations')
                else:
                    django_messages.warning(request, 
                        f'Your message contained inappropriate content. Warning {warning_count}/2. One more warning and you will be blocked.')
            
            return redirect('message_thread', recipient_id=recipient.id)
    else:
        form = MessageForm()
    
    return render(request, 'mainpage/message_thread.html', {
        'sender': sender,
        'recipient': recipient,
        'messages': messages_list,
        'form': form,
        'is_blocked': is_blocked
    })


@login_required(login_url='student_login')
def send_message(request, recipient_id):
    """Send a message (API endpoint for AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Get student profile safely
    if not hasattr(request.user, 'student_profile') or request.user.student_profile is None:
        return JsonResponse({'error': 'Only students can send messages'}, status=403)
    
    sender = request.user.student_profile
    recipient = get_object_or_404(Student, id=recipient_id)
    
    # Check if in same club
    if sender.club != recipient.club:
        return JsonResponse({'error': 'You can only message members in your club'}, status=403)
    
    # Check if blocked
    is_blocked = BlockedUser.objects.filter(
        Q(blocked_by=sender, blocked_user=recipient) | Q(blocked_by=recipient, blocked_user=sender)
    ).exists()
    
    if is_blocked:
        return JsonResponse({'error': 'Cannot message this user'}, status=403)
    
    form = MessageForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({'error': form.errors.as_text()}, status=400)

    content = form.cleaned_data['content'].strip()
    
    # Check for bad words
    has_bad_words = contains_bad_words(content)
    
    message = form.save(commit=False)
    message.content = content
    message.sender = sender
    message.recipient = recipient
    message.contains_warning = has_bad_words
    message.save()

    response_payload = {
        'success': True,
        'message_id': message.id,
        'attachment_url': message.attachment.url if message.attachment else '',
        'attachment_name': message.attachment_name,
    }
    
    if has_bad_words:
        # Add warning to sender
        warning_count = add_warning(sender, f"Sent message with inappropriate content")
        
        if should_block_user(warning_count):
            # Block the user
            BlockedUser.objects.get_or_create(blocked_by=recipient, blocked_user=sender)
            return JsonResponse({
                'warning': f'Your message contained inappropriate content. You received {warning_count} warnings and have been BLOCKED.',
                'blocked': True
            }, status=400)
        else:
            return JsonResponse({
                'warning': f'Your message contained inappropriate content. Warning {warning_count}/2.',
                'message_id': message.id,
                'attachment_url': response_payload['attachment_url'],
                'attachment_name': response_payload['attachment_name'],
            }, status=201)
    
    return JsonResponse(response_payload, status=201)


@login_required(login_url='student_login')
def get_available_users(request):
    """Get list of users available to message (same club + not blocked)"""
    # Get student profile safely
    if not hasattr(request.user, 'student_profile') or request.user.student_profile is None:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'users': []})
        return JsonResponse({'error': 'Only students can access this'}, status=403)
    
    student = request.user.student_profile
    
    # Get all students in same club except self
    available_users = student.club.students.exclude(id=student.id).select_related('user')
    
    # Filter out blocked users
    blocked_ids = BlockedUser.objects.filter(
        Q(blocked_by=student) | Q(blocked_user=student)
    ).values_list('blocked_user_id', 'blocked_by_id')
    
    blocked_ids_set = set()
    for blocked_by_id, blocked_user_id in blocked_ids:
        blocked_ids_set.add(blocked_by_id)
        blocked_ids_set.add(blocked_user_id)
    
    available_users = available_users.exclude(id__in=blocked_ids_set)
    
    data = [{'id': user.id, 'name': user.name} for user in available_users]
    return JsonResponse({'users': data})


# ==================== PASSWORD RESET VIEWS ====================

def forgot_password(request):
    """View for initiating password reset process"""
    if request.user.is_authenticated:
        return role_redirect(request.user)
    
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                # Get the first user with this email (handles multiple users with same email)
                user = User.objects.filter(email=email).first()
                
                if user:
                    token, otp = create_password_reset_request(user)
                    
                    if token and otp:
                        # Send email with OTP
                        email_sent = send_password_reset_email(email, otp, token)
                        if email_sent:
                            django_messages.success(request, 'OTP has been sent to your email. Please check your inbox.')
                            return redirect('password_reset_verify', token=token)
                        else:
                            django_messages.error(request, 'Failed to send email. Please try again later.')
                    else:
                        django_messages.error(request, 'Failed to create reset request. Please try again.')
                else:
                    # Don't reveal if email exists for security
                    django_messages.info(request, 'If an account exists with this email, you will receive a password reset link.')
                    return redirect('password_reset_verify', token='invalid')
            except Exception as e:
                # Handle any other errors
                django_messages.error(request, 'An error occurred. Please try again later.')
                return redirect('password_reset_verify', token='invalid')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'mainpage/forgot_password.html', {'form': form})


def password_reset_verify(request, token):
    """View for verifying OTP and resetting password"""
    if request.user.is_authenticated:
        return role_redirect(request.user)
    
    if request.method == 'POST':
        otp_form = PasswordResetOTPForm(request.POST)
        password_form = PasswordResetForm(request.POST)
        
        if 'verify_otp' in request.POST:
            # Verify OTP step
            if otp_form.is_valid():
                otp = otp_form.cleaned_data['otp']
                reset_request = verify_otp_and_get_reset_request(token, otp)
                
                if reset_request:
                    django_messages.success(request, 'OTP verified! Now set your new password.')
                    return redirect('password_reset_confirm', token=token, step='password')
                else:
                    django_messages.error(request, 'Invalid or expired OTP. Please try again.')
        
        elif 'set_password' in request.POST:
            # Set new password step
            if password_form.is_valid():
                new_password = password_form.cleaned_data['new_password']
                
                # Verify token is still valid
                from .models import PasswordReset
                from django.utils import timezone
                try:
                    reset_request = PasswordReset.objects.get(
                        token=token,
                        is_used=False,
                        expires_at__gt=timezone.now()
                    )
                    
                    if reset_user_password(reset_request, new_password):
                        django_messages.success(request, 'Password reset successful! Please login with your new password.')
                        return redirect('student_login')
                    else:
                        django_messages.error(request, 'Failed to reset password. Please try again.')
                except PasswordReset.DoesNotExist:
                    django_messages.error(request, 'Reset token expired. Please request a new password reset.')
                    return redirect('forgot_password')
    else:
        otp_form = PasswordResetOTPForm()
        password_form = PasswordResetForm()
    
    return render(request, 'mainpage/password_reset_verify.html', {
        'token': token,
        'otp_form': otp_form,
        'password_form': password_form
    })


def password_reset_confirm(request, token, step='otp'):
    """Confirm password reset with OTP verification"""
    if request.user.is_authenticated:
        return role_redirect(request.user)
    
    from .models import PasswordReset
    from django.utils import timezone
    
    try:
        reset_request = PasswordReset.objects.get(
            token=token,
            is_used=False,
            expires_at__gt=timezone.now()
        )
    except PasswordReset.DoesNotExist:
        django_messages.error(request, 'Reset link has expired. Please request a new password reset.')
        return redirect('forgot_password')
    
    if step == 'otp':
        if request.method == 'POST':
            form = PasswordResetOTPForm(request.POST)
            if form.is_valid():
                otp = form.cleaned_data['otp']
                if reset_request.otp == otp:
                    return redirect('password_reset_confirm', token=token, step='password')
                else:
                    django_messages.error(request, 'Invalid OTP. Please try again.')
        else:
            form = PasswordResetOTPForm()
        return render(request, 'mainpage/password_reset_confirm.html', {'form': form, 'step': 'otp'})
    
    elif step == 'password':
        if request.method == 'POST':
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                new_password = form.cleaned_data['new_password']
                if reset_user_password(reset_request, new_password):
                    django_messages.success(request, 'Password reset successful! Please login with your new password.')
                    return redirect('student_login')
                else:
                    django_messages.error(request, 'Failed to reset password. Please try again.')
        else:
            form = PasswordResetForm()
        return render(request, 'mainpage/password_reset_confirm.html', {'form': form, 'step': 'password'})



@login_required(login_url='admin_login')
def admin_edit_student_password(request, student_id):
    """Allow admin to edit student password"""
    if not hasattr(request.user, 'managed_club'):
        django_messages.error(request, 'Only club admins can edit student passwords.')
        return redirect('admin_login')
    
    club = request.user.managed_club
    try:
        student = club.students.get(id=student_id)
    except Student.DoesNotExist:
        django_messages.error(request, 'Student not found.')
        return redirect('club_dashboard')
    
    form = AdminPasswordEditForm(request.POST or None, user=student.user)
    if request.method == 'POST':
        if form.is_valid():
            student.user.set_password(form.cleaned_data['new_password'])
            student.user.save()
            django_messages.success(request, f'Password for {student.name} has been updated.')
            return redirect('club_dashboard')
        django_messages.error(request, 'Please choose a stronger password.')
    
    return render(request, 'mainpage/admin_edit_student_password.html', {'student': student, 'form': form})


@login_required(login_url='student_login')
def block_user(request, user_id):
    """Block a user from messaging"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Get student profile safely
    if not hasattr(request.user, 'student_profile') or request.user.student_profile is None:
        return JsonResponse({'error': 'Only students can block users'}, status=403)
    
    student = request.user.student_profile
    user_to_block = get_object_or_404(Student, id=user_id)
    
    # Create block relationship (blocking prevents them from messaging us)
    BlockedUser.objects.get_or_create(blocked_by=student, blocked_user=user_to_block)
    
    django_messages.success(request, f'{user_to_block.name} has been blocked.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('view_conversations')


@login_required(login_url='student_login')
def unblock_user(request, user_id):
    """Unblock a user"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Get student profile safely
    if not hasattr(request.user, 'student_profile') or request.user.student_profile is None:
        return JsonResponse({'error': 'Only students can unblock users'}, status=403)
    
    student = request.user.student_profile
    user_to_unblock = get_object_or_404(Student, id=user_id)
    
    BlockedUser.objects.filter(blocked_by=student, blocked_user=user_to_unblock).delete()
    
    django_messages.success(request, f'{user_to_unblock.name} has been unblocked.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('view_conversations')


@login_required(login_url='student_login')
def view_user_warnings(request):
    """View warnings received by current student"""
    # Get student profile safely
    if not hasattr(request.user, 'student_profile') or request.user.student_profile is None:
        django_messages.error(request, 'Only students can view warnings.')
        return redirect('student_login')
    
    student = request.user.student_profile
    warnings = student.warnings.order_by('-created_at')
    
    return render(request, 'mainpage/user_warnings.html', {
        'student': student,
        'warnings': warnings
    })
