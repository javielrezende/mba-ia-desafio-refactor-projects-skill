"""Gate de autenticação e autorização (RP-17).

A primeira passagem desta refatoração tratou o finding 4 só pela metade: hash
scrypt, seed hasheado, `/admin/query` e `/admin/reset-db` removidos — e nenhuma
das 17 rotas restantes exigindo credencial. `GET /relatorios/vendas` seguia
devolvendo o faturamento da operação para `curl` sem header nenhum, que é
exatamente o impacto descrito no próprio finding.

O guard **vale sempre**. Não existe `AUTH_REQUIRED`: o ambiente escolhe *qual*
chave assina o token e por *quanto tempo* ele vale, nunca *se* a verificação
acontece. Controle desligado por default é controle ausente com uma camada de
disfarce a mais.

Exigir credencial quebra quem chamava a API anonimamente. É breaking change de
segurança, da mesma família da remoção do campo `senha` da resposta: vai listado
em *Breaking changes* no relatório e é feito assim mesmo.

As rotas públicas — e o motivo de cada uma — estão em `views/routes.py`.
"""
from functools import wraps

from flask import current_app, g, request

from src.config.constants import TipoUsuario
from src.domain.errors import AutenticacaoError, PermissaoError

PREFIXO_BEARER = "Bearer "


def _payload_do_header():
    cabecalho = request.headers.get("Authorization", "")
    if not cabecalho.startswith(PREFIXO_BEARER):
        return None
    token = cabecalho[len(PREFIXO_BEARER):].strip()
    return current_app.extensions["token_signer"].decodificar(token)


def _exigir_identidade():
    """Resolve o chamador. Sem token válido, 401 — sem exceção e sem flag."""
    payload = _payload_do_header()
    if not payload:
        raise AutenticacaoError()
    g.autenticado = payload
    return payload


def _e_admin(payload):
    return payload.get("tipo") == TipoUsuario.ADMIN.value


def exigir_autenticacao(handler):
    """Exige token válido de qualquer usuário."""

    @wraps(handler)
    def wrapper(*args, **kwargs):
        _exigir_identidade()
        return handler(*args, **kwargs)

    return wrapper


def exigir_admin(handler):
    """Exige token válido de um administrador.

    É o guard do relatório de faturamento, da listagem global de usuários e de
    pedidos e da escrita no catálogo — o dado agregado da operação e o dado de
    terceiros.
    """

    @wraps(handler)
    def wrapper(*args, **kwargs):
        payload = _exigir_identidade()
        if not _e_admin(payload):
            raise PermissaoError("Requer privilégio de administrador")
        return handler(*args, **kwargs)

    return wrapper


def exigir_dono_ou_admin(parametro):
    """Restringe a rota ao dono do recurso ou a um admin.

    Sem isto, "autenticado" bastaria para ler o cadastro e o histórico de compra
    de qualquer outro cliente: token de conta comum continua sendo credencial
    válida.
    """

    def decorador(handler):
        @wraps(handler)
        def wrapper(*args, **kwargs):
            payload = _exigir_identidade()
            if not _e_admin(payload) and payload.get("sub") != kwargs.get(parametro):
                raise PermissaoError("Acesso restrito ao próprio usuário")
            return handler(*args, **kwargs)

        return wrapper

    return decorador


def exigir_dono_no_corpo(campo):
    """Variante para o recurso cujo dono vem no corpo, não na URL.

    `POST /pedidos` carrega `usuario_id` no JSON: sem esta checagem, qualquer
    conta autenticada lançaria pedido — e baixa de estoque — em nome de outra.
    """

    def decorador(handler):
        @wraps(handler)
        def wrapper(*args, **kwargs):
            payload = _exigir_identidade()
            corpo = request.get_json(silent=True) or {}
            if not _e_admin(payload) and corpo.get(campo) != payload.get("sub"):
                raise PermissaoError("Só é possível criar pedido para o próprio usuário")
            return handler(*args, **kwargs)

        return wrapper

    return decorador
