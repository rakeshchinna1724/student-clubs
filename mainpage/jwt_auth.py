import base64
import hashlib
import hmac
import json
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone


JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_LIFETIME = timedelta(minutes=30)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)


class JWTError(ValueError):
    pass


def _b64encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')


def _b64decode(value):
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode('ascii'))


def _json_b64encode(payload):
    return _b64encode(json.dumps(payload, separators=(',', ':'), sort_keys=True).encode('utf-8'))


def _sign(unsigned_token):
    signature = hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        unsigned_token.encode('ascii'),
        hashlib.sha256,
    ).digest()
    return _b64encode(signature)


def get_user_role(user):
    if hasattr(user, 'managed_club'):
        return 'admin'
    if hasattr(user, 'student_profile'):
        return 'member'
    return None


def create_jwt(user, token_type='access'):
    now = timezone.now()
    lifetime = ACCESS_TOKEN_LIFETIME if token_type == 'access' else REFRESH_TOKEN_LIFETIME
    header = {'alg': JWT_ALGORITHM, 'typ': 'JWT'}
    payload = {
        'sub': str(user.pk),
        'username': user.username,
        'role': get_user_role(user),
        'type': token_type,
        'iat': int(now.timestamp()),
        'exp': int((now + lifetime).timestamp()),
        'jti': secrets.token_urlsafe(16),
    }
    unsigned_token = f'{_json_b64encode(header)}.{_json_b64encode(payload)}'
    return f'{unsigned_token}.{_sign(unsigned_token)}'


def decode_jwt(token, expected_type='access'):
    try:
        header_segment, payload_segment, signature = token.split('.')
    except ValueError as exc:
        raise JWTError('Invalid token format.') from exc

    unsigned_token = f'{header_segment}.{payload_segment}'
    if not hmac.compare_digest(_sign(unsigned_token), signature):
        raise JWTError('Invalid token signature.')

    try:
        header = json.loads(_b64decode(header_segment))
        payload = json.loads(_b64decode(payload_segment))
    except (json.JSONDecodeError, ValueError) as exc:
        raise JWTError('Invalid token payload.') from exc

    if header.get('alg') != JWT_ALGORITHM:
        raise JWTError('Unsupported token algorithm.')
    if payload.get('type') != expected_type:
        raise JWTError('Invalid token type.')
    if int(payload.get('exp', 0)) < int(timezone.now().timestamp()):
        raise JWTError('Token has expired.')
    return payload


def authenticate_jwt_request(request, expected_type='access'):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise JWTError('Missing bearer token.')

    payload = decode_jwt(auth_header.removeprefix('Bearer ').strip(), expected_type=expected_type)
    try:
        user = User.objects.get(pk=payload['sub'], is_active=True)
    except (KeyError, User.DoesNotExist) as exc:
        raise JWTError('Token user was not found.') from exc
    return user, payload
