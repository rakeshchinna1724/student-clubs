import json

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .jwt_auth import JWTError, authenticate_jwt_request, create_jwt, decode_jwt, get_user_role
from .models import Club, Student


def _json_body(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return None


def _validation_error_response(error):
    if hasattr(error, 'messages'):
        errors = error.messages
    else:
        errors = [str(error)]
    return JsonResponse({'errors': errors}, status=400)


def _user_payload(user):
    role = get_user_role(user)
    payload = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': role,
    }
    if role == 'admin':
        payload['club'] = {'id': user.managed_club.id, 'name': user.managed_club.name}
    elif role == 'member':
        student = user.student_profile
        payload['profile'] = {
            'id': student.id,
            'name': student.name,
            'age': student.age,
            'department': student.department,
            'club': {'id': student.club.id, 'name': student.club.name} if student.club else None,
        }
    return payload


def jwt_required(roles=None):
    allowed_roles = set(roles or [])

    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            try:
                request.jwt_user, request.jwt_payload = authenticate_jwt_request(request)
            except JWTError as exc:
                return JsonResponse({'error': str(exc)}, status=401)

            role = get_user_role(request.jwt_user)
            if allowed_roles and role not in allowed_roles:
                return JsonResponse({'error': 'You do not have permission to access this resource.'}, status=403)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


@csrf_exempt
@require_POST
def api_register(request):
    body = _json_body(request)
    if body is None:
        return JsonResponse({'error': 'Request body must be valid JSON.'}, status=400)

    role = body.get('role')
    username = (body.get('username') or '').strip()
    email = (body.get('email') or '').strip()
    password = body.get('password') or ''

    if role not in {'admin', 'member'}:
        return JsonResponse({'error': 'Role must be either "admin" or "member".'}, status=400)
    if not username or not email or not password:
        return JsonResponse({'error': 'Username, email, and password are required.'}, status=400)
    if User.objects.filter(username__iexact=username).exists():
        return JsonResponse({'error': 'This username is already taken.'}, status=400)
    if role == 'admin' and not (body.get('club_name') or '').strip():
        return JsonResponse({'error': 'club_name is required for admin registration.'}, status=400)
    if role == 'member':
        required_fields = ['name', 'age', 'department', 'club_id']
        missing_fields = [field for field in required_fields if body.get(field) in (None, '')]
        if missing_fields:
            return JsonResponse({'error': f'Missing required fields: {", ".join(missing_fields)}.'}, status=400)

    try:
        validate_password(password, user=User(username=username, email=email))
    except ValidationError as exc:
        return _validation_error_response(exc)

    try:
        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=password)

            if role == 'admin':
                club_name = (body.get('club_name') or '').strip()
                Club.objects.create(name=club_name, admin=user)
            else:
                club = Club.objects.get(pk=body['club_id'])
                Student.objects.create(
                    user=user,
                    club=club,
                    name=str(body['name']).strip(),
                    email=email,
                    age=body['age'],
                    department=str(body['department']).strip(),
                )
    except Club.DoesNotExist:
        return JsonResponse({'error': 'Selected club does not exist.'}, status=400)
    except (IntegrityError, ValueError) as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    return JsonResponse({
        'user': _user_payload(user),
        'tokens': {
            'access': create_jwt(user, 'access'),
            'refresh': create_jwt(user, 'refresh'),
        },
    }, status=201)


@csrf_exempt
@require_POST
def api_login(request):
    body = _json_body(request)
    if body is None:
        return JsonResponse({'error': 'Request body must be valid JSON.'}, status=400)

    user = authenticate(request, username=body.get('username'), password=body.get('password'))
    if user is None:
        return JsonResponse({'error': 'Invalid username or password.'}, status=401)

    role = get_user_role(user)
    requested_role = body.get('role')
    if requested_role and requested_role != role:
        return JsonResponse({'error': f'This account is not a {requested_role} account.'}, status=403)

    return JsonResponse({
        'user': _user_payload(user),
        'tokens': {
            'access': create_jwt(user, 'access'),
            'refresh': create_jwt(user, 'refresh'),
        },
    })


@csrf_exempt
@require_POST
def api_refresh(request):
    body = _json_body(request)
    if body is None:
        return JsonResponse({'error': 'Request body must be valid JSON.'}, status=400)

    try:
        payload = decode_jwt(body.get('refresh', ''), expected_type='refresh')
        user = User.objects.get(pk=payload['sub'], is_active=True)
    except (JWTError, User.DoesNotExist) as exc:
        return JsonResponse({'error': str(exc)}, status=401)

    return JsonResponse({'access': create_jwt(user, 'access')})


@require_GET
@jwt_required()
def api_me(request):
    return JsonResponse({'user': _user_payload(request.jwt_user)})


@require_GET
@jwt_required(roles=['admin'])
def api_admin_summary(request):
    club = request.jwt_user.managed_club
    return JsonResponse({
        'club': {'id': club.id, 'name': club.name},
        'members_count': club.students.count(),
        'posts_count': club.posts.count(),
        'events_count': club.events.count(),
        'announcements_count': club.announcements.count(),
    })


@require_GET
@jwt_required(roles=['member'])
def api_member_profile(request):
    return JsonResponse({'user': _user_payload(request.jwt_user)})


@require_GET
def get_college_clubs(request, college_id):
    """Get all clubs for a specific college"""
    from django.db.models import Count
    
    try:
        college_id = int(college_id)
        clubs = Club.objects.filter(
            college_id=college_id
        ).annotate(
            member_count=Count('students', distinct=True)
        ).order_by('name').values('id', 'name', 'member_count')
        
        return JsonResponse({
            'clubs': list(clubs),
            'count': len(list(clubs))
        })
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid college ID'}, status=400)
