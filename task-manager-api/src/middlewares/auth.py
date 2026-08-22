"""Middleware de autenticação e autorização.

A API original não verificava token em nenhuma das 22 rotas e tinha um
User.is_admin() definido e nunca chamado (finding 2 / AP-04). Aqui a verificação
existe de fato e usa is_admin().

Fica desligada por default (AUTH_REQUIRED=false) porque exigir token quebraria
os 22 endpoints existentes, muito além das duas breaking changes aprovadas.
Basta AUTH_REQUIRED=true no .env para passar a exigir Authorization: Bearer.
"""
from functools import wraps

from flask import g, request

from src.config.constants import Role
from src.domain.errors import ForbiddenError, UnauthorizedError
from src.infrastructure.security import decode_token


def _current_payload():
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None
    return decode_token(header[len('Bearer '):].strip())


def require_auth(settings):
    """Exige token válido quando settings.AUTH_REQUIRED estiver ligado."""

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            payload = _current_payload()
            g.auth_payload = payload
            if settings.AUTH_REQUIRED and not payload:
                raise UnauthorizedError('Autenticação obrigatória')
            return view(*args, **kwargs)

        return wrapper

    return decorator


def require_admin(settings):
    """Exige papel de administrador quando a autenticação está ligada."""

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            payload = _current_payload()
            g.auth_payload = payload
            if settings.AUTH_REQUIRED:
                if not payload:
                    raise UnauthorizedError('Autenticação obrigatória')
                if payload.get('role') != 'admin':
                    raise ForbiddenError('Requer privilégio de administrador')
            return view(*args, **kwargs)

        return wrapper

    return decorator


def _require_identity(settings):
    """Resolve o chamador e exige token quando a autenticação está ligada."""
    payload = _current_payload()
    g.auth_payload = payload
    if settings.AUTH_REQUIRED and not payload:
        raise UnauthorizedError('Autenticação obrigatória')
    return payload


def _is_admin(payload) -> bool:
    return bool(payload) and payload.get('role') == Role.ADMIN.value


def require_self_or_admin(settings, param='user_id'):
    """Restringe a alteração de um usuário ao próprio dono ou a um admin.

    Sem isso, qualquer chamador autenticado editava o registro de qualquer
    outro usuário — era o `PUT /users/<id>` aberto apontado na análise manual.
    """

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            payload = _require_identity(settings)
            if settings.AUTH_REQUIRED:
                target_id = kwargs.get(param)
                if not _is_admin(payload) and payload.get('sub') != target_id:
                    raise ForbiddenError('Só é possível alterar o próprio usuário')
            return view(*args, **kwargs)

        return wrapper

    return decorator


def require_admin_for_role(settings, allow_default=False):
    """Impede que um não-admin defina ou altere o campo `role`.

    Este era o vetor de escalada de privilégio: `PUT /users/<id>` com
    `{"role": "admin"}` promovia o próprio chamador, e `POST /users` permitia
    registrar-se já como admin. A validação anterior conferia se o valor de
    `role` era válido, nunca *quem* podia defini-lo.

    `allow_default=True` (usado no registro) libera o papel padrão `user`, para
    que a criação de conta comum siga aberta.
    """

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if settings.AUTH_REQUIRED:
                body = request.get_json(silent=True) or {}
                requested_role = body.get('role')
                privileged = requested_role is not None and not (
                    allow_default and requested_role == Role.USER.value
                )
                if privileged:
                    payload = _require_identity(settings)
                    if not _is_admin(payload):
                        raise ForbiddenError(
                            'Apenas administradores podem definir o papel do usuário'
                        )
            return view(*args, **kwargs)

        return wrapper

    return decorator
