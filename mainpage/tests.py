import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import EventForm, MessageForm
from .models import Club, College, CollegeAdmin, Event, EventRSVP, Message, Student


class JWTAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.club_admin = User.objects.create_user(
            username='club-admin',
            email='admin@example.com',
            password='StrongPass123!',
        )
        self.club = Club.objects.create(name='Robotics Club', admin=self.club_admin)

    def post_json(self, url_name, payload):
        return self.client.post(
            reverse(url_name),
            data=json.dumps(payload),
            content_type='application/json',
        )

    def auth_get(self, url_name, access_token):
        return self.client.get(
            reverse(url_name),
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )

    def test_member_can_register_and_receives_tokens(self):
        response = self.post_json('api_register', {
            'role': 'member',
            'username': 'new-member',
            'email': 'member@example.com',
            'password': 'StrongPass123!',
            'name': 'New Member',
            'age': 20,
            'department': 'Computer Science',
            'club_id': self.club.id,
        })

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['user']['role'], 'member')
        self.assertIn('access', data['tokens'])
        self.assertTrue(Student.objects.filter(user__username='new-member', club=self.club).exists())

    def test_weak_password_is_rejected_on_register(self):
        response = self.post_json('api_register', {
            'role': 'admin',
            'username': 'weak-admin',
            'email': 'weak@example.com',
            'password': 'password',
            'club_name': 'Chess Club',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.json())
        self.assertFalse(User.objects.filter(username='weak-admin').exists())

    def test_login_returns_role_and_tokens(self):
        response = self.post_json('api_login', {
            'username': 'club-admin',
            'password': 'StrongPass123!',
            'role': 'admin',
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['user']['role'], 'admin')
        self.assertEqual(data['user']['club']['name'], 'Robotics Club')
        self.assertIn('refresh', data['tokens'])

    def test_protected_endpoint_requires_valid_jwt(self):
        missing_token_response = self.client.get(reverse('api_me'))
        self.assertEqual(missing_token_response.status_code, 401)

        login_response = self.post_json('api_login', {
            'username': 'club-admin',
            'password': 'StrongPass123!',
        })
        token = login_response.json()['tokens']['access']
        response = self.auth_get('api_me', token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['username'], 'club-admin')

    def test_role_based_access_denies_member_from_admin_summary(self):
        member_user = User.objects.create_user(
            username='member',
            email='member2@example.com',
            password='StrongPass123!',
        )
        Student.objects.create(
            user=member_user,
            club=self.club,
            name='Club Member',
            email='member2@example.com',
            age=21,
            department='Physics',
        )
        login_response = self.post_json('api_login', {
            'username': 'member',
            'password': 'StrongPass123!',
        })
        token = login_response.json()['tokens']['access']

        response = self.auth_get('api_admin_summary', token)

        self.assertEqual(response.status_code, 403)


class BaseTemplateRoleTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_base_template_marks_college_admin_role(self):
        user = User.objects.create_user(
            username='college-admin',
            email='college-admin@example.com',
            password='StrongPass123!',
        )
        college = College.objects.create(
            name='Example College',
            email='college@example.com',
            admin_name='College Admin',
            phone='1234567890',
            address='123 Campus Road',
            city='Campus City',
            state='Campus State',
            pincode='123456',
            registration_number='EX-123',
        )
        CollegeAdmin.objects.create(user=user, college=college)

        rendered = render_to_string('mainpage/base.html', {'user': user})

        self.assertIn('data-user-role="college-admin"', rendered)

    def test_college_admin_available_users_ajax_is_empty(self):
        user = User.objects.create_user(
            username='college-admin',
            email='college-admin@example.com',
            password='StrongPass123!',
        )
        college = College.objects.create(
            name='Example College',
            email='college@example.com',
            admin_name='College Admin',
            phone='1234567890',
            address='123 Campus Road',
            city='Campus City',
            state='Campus State',
            pincode='123456',
            registration_number='EX-123',
        )
        CollegeAdmin.objects.create(user=user, college=college)

        self.client.login(username='college-admin', password='StrongPass123!')
        response = self.client.get(
            reverse('get_available_users'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'users': []})

    def test_homepage_shows_separate_role_portal_links(self):
        rendered = render_to_string('mainpage/index.html', {
            'is_college_authenticated': False,
            'user': AnonymousUser(),
        })

        self.assertIn(reverse('college_login'), rendered)
        self.assertIn(reverse('college_register'), rendered)
        self.assertIn(reverse('public_colleges'), rendered)
        self.assertIn(reverse('student_login'), rendered)
        self.assertIn(reverse('student_signup'), rendered)
        self.assertIn(reverse('admin_login'), rendered)
        self.assertNotIn(reverse('admin_signup'), rendered)

    def test_logged_out_user_cannot_open_club_creation(self):
        response = self.client.get(reverse('admin_signup'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('college_login'))

    def test_college_admin_can_create_club_without_switching_accounts(self):
        user = User.objects.create_user(
            username='college-admin',
            email='college-admin@example.com',
            password='StrongPass123!',
        )
        college = College.objects.create(
            name='Example College',
            email='college@example.com',
            admin_name='College Admin',
            phone='1234567890',
            address='123 Campus Road',
            city='Campus City',
            state='Campus State',
            pincode='123456',
            registration_number='EX-123',
        )
        CollegeAdmin.objects.create(user=user, college=college)

        self.client.login(username='college-admin', password='StrongPass123!')
        response = self.client.post(reverse('admin_signup'), {
            'username': 'robotics-admin',
            'email': 'robotics-admin@example.com',
            'club_name': 'Robotics',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('college_dashboard'))
        self.assertTrue(Club.objects.filter(name='Robotics', college=college).exists())
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

    def test_public_colleges_page_lists_live_colleges(self):
        from .views import public_colleges

        college_admin = User.objects.create_user(
            username='college-admin',
            email='college-admin@example.com',
            password='StrongPass123!',
        )
        college = College.objects.create(
            name='Live College',
            email='live-college@example.com',
            admin_name='College Admin',
            phone='1234567890',
            address='123 Campus Road',
            city='Campus City',
            state='Campus State',
            pincode='123456',
            registration_number='LIVE-123',
        )
        CollegeAdmin.objects.create(user=college_admin, college=college)
        club_admin = User.objects.create_user(
            username='club-admin-live',
            email='club-admin-live@example.com',
            password='StrongPass123!',
        )
        Club.objects.create(name='Robotics', admin=club_admin, college=college)

        request = self.factory.get(reverse('public_colleges'))
        request.user = AnonymousUser()
        response = public_colleges(request)
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn('Live College', content)
        self.assertIn(reverse('public_college_detail', args=[college.id]), content)

    def test_public_college_detail_lists_clubs_and_members(self):
        from .views import public_college_detail

        college_admin = User.objects.create_user(
            username='college-admin',
            email='college-admin@example.com',
            password='StrongPass123!',
        )
        college = College.objects.create(
            name='Live College',
            email='live-college@example.com',
            admin_name='College Admin',
            phone='1234567890',
            address='123 Campus Road',
            city='Campus City',
            state='Campus State',
            pincode='123456',
            registration_number='LIVE-123',
        )
        CollegeAdmin.objects.create(user=college_admin, college=college)
        club_admin = User.objects.create_user(
            username='club-admin-live',
            email='club-admin-live@example.com',
            password='StrongPass123!',
        )
        club = Club.objects.create(name='Robotics', admin=club_admin, college=college)
        student_user = User.objects.create_user(
            username='student-live',
            email='student-live@example.com',
            password='StrongPass123!',
        )
        Student.objects.create(
            user=student_user,
            club=club,
            name='Student Live',
            email='student-live@example.com',
            age=20,
            department='Computer Science',
        )

        request = self.factory.get(reverse('public_college_detail', args=[college.id]))
        request.user = AnonymousUser()
        response = public_college_detail(request, college.id)
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn('Live College', content)
        self.assertIn('Robotics', content)
        self.assertIn('Student Live', content)
        self.assertIn('Computer Science', content)

    def test_college_admin_cannot_open_student_signup(self):
        user = User.objects.create_user(
            username='college-admin',
            email='college-admin@example.com',
            password='StrongPass123!',
        )
        college = College.objects.create(
            name='Example College',
            email='college@example.com',
            admin_name='College Admin',
            phone='1234567890',
            address='123 Campus Road',
            city='Campus City',
            state='Campus State',
            pincode='123456',
            registration_number='EX-123',
        )
        CollegeAdmin.objects.create(user=user, college=college)

        self.client.login(username='college-admin', password='StrongPass123!')
        response = self.client.get(reverse('student_signup'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('college_dashboard'))


class EventManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='event-admin',
            email='event-admin@example.com',
            password='StrongPass123!',
        )
        self.club = Club.objects.create(name='Science Club', admin=self.admin_user)
        self.member_user = User.objects.create_user(
            username='event-member',
            email='event-member@example.com',
            password='StrongPass123!',
        )
        self.student = Student.objects.create(
            user=self.member_user,
            club=self.club,
            name='Event Member',
            email='event-member@example.com',
            age=19,
            department='Biology',
        )

    def test_admin_can_create_update_and_delete_event(self):
        self.client.login(username='event-admin', password='StrongPass123!')
        event_file = SimpleUploadedFile('agenda.pdf', b'event agenda', content_type='application/pdf')
        create_response = self.client.post(reverse('create_event'), {
            'title': 'Research Meetup',
            'description': 'Discuss upcoming research projects.',
            'event_type': 'meeting',
            'event_date': (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'),
            'location': 'Room 204',
            'attachment': event_file,
        })

        self.assertEqual(create_response.status_code, 302)
        event = Event.objects.get(title='Research Meetup')
        self.assertEqual(event.location, 'Room 204')
        self.assertTrue(event.attachment.name.endswith('.pdf'))

        update_response = self.client.post(reverse('update_event', args=[event.id]), {
            'title': 'Research Planning Meetup',
            'description': 'Discuss updated research plans.',
            'event_type': 'seminar',
            'event_date': (timezone.now() + timedelta(days=4)).strftime('%Y-%m-%dT%H:%M'),
            'location': 'Auditorium',
        })

        self.assertEqual(update_response.status_code, 302)
        event.refresh_from_db()
        self.assertEqual(event.title, 'Research Planning Meetup')
        self.assertEqual(event.location, 'Auditorium')

        delete_response = self.client.post(reverse('delete_event', args=[event.id]))

        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(Event.objects.filter(id=event.id).exists())

    def test_event_attachment_rejects_unsupported_file_type(self):
        form = EventForm(data={
            'title': 'Unsafe File Event',
            'description': 'This upload should fail.',
            'event_type': 'meeting',
            'event_date': (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'),
            'location': 'Room 204',
        }, files={
            'attachment': SimpleUploadedFile('script.exe', b'bad', content_type='application/octet-stream'),
        })

        self.assertFalse(form.is_valid())
        self.assertIn('attachment', form.errors)

    def test_member_can_rsvp_yes_or_no_once_per_event(self):
        event = Event.objects.create(
            club=self.club,
            created_by=self.admin_user,
            title='Lab Tour',
            description='Tour the new lab.',
            event_type='workshop',
            event_date=timezone.now() + timedelta(days=2),
            location='Science Block',
        )
        self.client.login(username='event-member', password='StrongPass123!')

        yes_response = self.client.post(reverse('rsvp_event', args=[event.id]), {'response': 'yes'})
        no_response = self.client.post(reverse('rsvp_event', args=[event.id]), {'response': 'no'})

        self.assertEqual(yes_response.status_code, 302)
        self.assertEqual(no_response.status_code, 302)
        self.assertEqual(EventRSVP.objects.filter(event=event, student=self.student).count(), 1)
        self.assertEqual(EventRSVP.objects.get(event=event, student=self.student).response, EventRSVP.RESPONSE_NO)

    def test_student_cannot_rsvp_to_another_club_event(self):
        other_admin = User.objects.create_user(username='other-admin', password='StrongPass123!')
        other_club = Club.objects.create(name='Other Club', admin=other_admin)
        event = Event.objects.create(
            club=other_club,
            created_by=other_admin,
            title='Other Event',
            description='A different club event.',
            event_type='other',
            event_date=timezone.now() + timedelta(days=1),
            location='Elsewhere',
        )
        self.client.login(username='event-member', password='StrongPass123!')

        response = self.client.post(reverse('rsvp_event', args=[event.id]), {'response': 'yes'})

        self.assertEqual(response.status_code, 302)
        self.assertFalse(EventRSVP.objects.filter(event=event, student=self.student).exists())


class MessageAttachmentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(username='chat-admin', password='StrongPass123!')
        self.club = Club.objects.create(name='Design Club', admin=self.admin_user)
        self.sender_user = User.objects.create_user(username='sender', password='StrongPass123!')
        self.recipient_user = User.objects.create_user(username='recipient', password='StrongPass123!')
        self.sender = Student.objects.create(
            user=self.sender_user,
            club=self.club,
            name='Sender',
            email='sender@example.com',
            age=20,
            department='Design',
        )
        self.recipient = Student.objects.create(
            user=self.recipient_user,
            club=self.club,
            name='Recipient',
            email='recipient@example.com',
            age=21,
            department='Design',
        )

    def test_student_can_send_file_only_message(self):
        self.client.login(username='sender', password='StrongPass123!')
        response = self.client.post(reverse('message_thread', args=[self.recipient.id]), {
            'content': '',
            'attachment': SimpleUploadedFile('notes.txt', b'hello', content_type='text/plain'),
        })

        self.assertEqual(response.status_code, 302)
        message = Message.objects.get(sender=self.sender, recipient=self.recipient)
        self.assertEqual(message.content, '')
        self.assertTrue(message.attachment.name.endswith('.txt'))

    def test_message_attachment_rejects_unsupported_file_type(self):
        form = MessageForm(data={
            'content': 'see attached',
        }, files={
            'attachment': SimpleUploadedFile('payload.exe', b'bad', content_type='application/octet-stream'),
        })

        self.assertFalse(form.is_valid())
        self.assertIn('attachment', form.errors)
