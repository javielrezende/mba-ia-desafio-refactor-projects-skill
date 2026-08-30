"""Middleware de autenticação e autorização.

A API original não verificava token em nenhuma das 22 rotas e tinha um
`User.is_admin()` definido e nunca chamado (finding 2 / AP-04). Aqui a
verificação existe e **vale sempre**.

Não há flag. A primeira passagem desta refatoração construiu estes mesmos guards
e os deixou dentro de `if settings.AUTH_REQUIRED:`, com o default `false` — o que
mantinha `DELETE /users/<id>` aberto a qualquer um nos defaults versionados, isto
é, deixava o finding 2 inteiramente em aberto por trás de código que *parecia*
protegido. Exigir credencial é breaking change de segurança, da mesma família da
remoção do campo `password` da resposta: quebra clientes, é registrado em
*Breaking changes*, e é feito assim mesmo. Ver RP-04 no playbook da skill.

O que o ambiente configura é o *parâmetro* da verificação (`SECRET_KEY`,
`TOKEN_TTL_SECONDS`), nunca *se* ela acontece.

Rotas públicas, e o motivo de cada uma — a lista completa está em views/routes.py:
`POST /login` (emite o token), `POST /users` (registro; papel privilegiado segue
exigindo admin), `GET /` e `GET /health` (liveness, sem dado de negócio).
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


def _require_identity():
    """Resolve o chamador e exige token válido. Sem token, 401 — sem exceção."""
    payload = _current_payload()
    if not payload:
        raise UnauthorizedError('Autenticação obrigatória')
    g.auth_payload = payload
    return payload


def _is_admin(payload) -> bool:
    return bool(payload) and payload.get('role') == Role.ADMIN.value


def require_auth(view):
    """Exige token válido. Usado como decorator direto, sem argumentos."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        _require_identity()
        return view(*args, **kwargs)

    return wrapper


def require_admin(view):
    """Exige token válido de um administrador."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        payload = _require_identity()
        if not _is_admin(payload):
            raise ForbiddenError('Requer privilégio de administrador')
        return view(*args, **kwargs)

    return wrapper


def require_self_or_admin(param='user_id'):
    """Restringe a alteração de um usuário ao próprio dono ou a um admin.

    Sem isso, qualquer chamador autenticado editava o registro de qualquer
    outro usuário — era o `PUT /users/<id>` aberto apontado na análise manual.
    """

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            payload = _require_identity()
            target_id = kwargs.get(param)
            if not _is_admin(payload) and payload.get('sub') != target_id:
                raise ForbiddenError('Só é possível alterar o próprio usuário')
            return view(*args, **kwargs)

        return wrapper

    return decorator


def require_admin_for_role(allow_default=False):
    """Impede que um não-admin defina ou altere o campo `role`.

    Este era o vetor de escalada de privilégio: `PUT /users/<id>` com
    `{"role": "admin"}` promovia o próprio chamador, e `POST /users` permitia
    registrar-se já como admin. A validação anterior conferia se o valor de
    `role` era válido, nunca *quem* podia defini-lo.

    `allow_default=True` (usado no registro) libera o papel padrão `user`, para
    que a criação de conta comum siga sendo a única escrita pública da API.
    """

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            body = request.get_json(silent=True) or {}
            requested_role = body.get('role')
            privileged = requested_role is not None and not (
                allow_default and requested_role == Role.USER.value
            )
            if privileged:
                payload = _require_identity()
                if not _is_admin(payload):
                    raise ForbiddenError(
                        'Apenas administradores podem definir o papel do usuário'
                    )
            return view(*args, **kwargs)

        return wrapper

    return decorator
