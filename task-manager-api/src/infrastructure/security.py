"""Hashing de senha e emissão/verificação de token.

Substitui o MD5 sem salt de models/user.py:29-32 e o token previsível
'fake-jwt-token-' + str(user.id) de routes/user_routes.py:210 (finding 2 / AP-04).

Nenhuma dependência nova: o hash usa werkzeug.security (scrypt, que já vem com o
Flask) e o token é um JWT HS256 montado com a stdlib (hmac + hashlib + base64),
que é exatamente a construção que a especificação HS256 define.
"""
import base64
import hashlib
import hmac
import json

from werkzeug.security import check_password_hash, generate_password_hash

from src.config.settings import settings
from src.infrastructure.clock import utc_now
from datetime import timedelta

#: Hash descartável com o mesmo custo de um hash real. Comparar contra ele quando
#: o e-mail não existe faz o login gastar o mesmo tempo nos dois caminhos, o que
#: fecha a enumeração de contas por tempo de resposta (finding 2 / AP-04).
DUMMY_PASSWORD_HASH = generate_password_hash('conta-inexistente')


def hash_password(raw_password: str) -> str:
    """Gera o hash salgado da senha (scrypt, via Werkzeug)."""
    return generate_password_hash(raw_password)


def verify_password(password_hash: str, raw_password: str) -> bool:
    """Verifica a senha em tempo constante contra o hash armazenado."""
    return check_password_hash(password_hash, raw_password)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('ascii')


def _b64url_decode(data: str) -> bytes:
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(signing_input: bytes) -> str:
    signature = hmac.new(settings.SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    return _b64url_encode(signature)


def issue_token(user_id: int, role: str) -> str:
    """Emite um JWT HS256 assinado, com expiração."""
    header = {'alg': 'HS256', 'typ': 'JWT'}
    expires_at = utc_now() + timedelta(seconds=settings.TOKEN_TTL_SECONDS)
    payload = {
        'sub': user_id,
        'role': role,
        'exp': int(expires_at.timestamp()),
    }
    segments = [
        _b64url_encode(json.dumps(header, separators=(',', ':')).encode()),
        _b64url_encode(json.dumps(payload, separators=(',', ':')).encode()),
    ]
    signing_input = '.'.join(segments).encode('ascii')
    segments.append(_sign(signing_input))
    return '.'.join(segments)


def decode_token(token: str) -> dict | None:
    """Devolve o payload se a assinatura confere e o token não expirou; senão None."""
    try:
        header_segment, payload_segment, signature = token.split('.')
    except (ValueError, AttributeError):
        return None

    signing_input = f'{header_segment}.{payload_segment}'.encode('ascii')
    if not hmac.compare_digest(_sign(signing_input), signature):
        return None

    try:
        payload = json.loads(_b64url_decode(payload_segment))
    except (ValueError, json.JSONDecodeError):
        return None

    if int(payload.get('exp', 0)) < int(utc_now().timestamp()):
        return None
    return payload
