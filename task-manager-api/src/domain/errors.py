"""Exceções de domínio.

Os services lançam estas exceções em vez de devolverem tuplas (corpo, status).
Assim a regra de negócio não conhece HTTP, e o error handler central
(src/middlewares/error_handler.py) faz a tradução para status — substituindo os
12 `except:` nus espalhados pelos handlers (finding 6 / AP-10).
"""


class DomainError(Exception):
    """Base de todo erro previsto pela regra de negócio."""

    status_code = 400
    message = 'Requisição inválida'

    def __init__(self, message: str | None = None):
        super().__init__(message or self.message)
        self.message = message or self.message


class ValidationError(DomainError):
    status_code = 400
    message = 'Dados inválidos'


class NotFoundError(DomainError):
    status_code = 404
    message = 'Recurso não encontrado'


class ConflictError(DomainError):
    status_code = 409
    message = 'Conflito de dados'


class UnauthorizedError(DomainError):
    status_code = 401
    message = 'Credenciais inválidas'


class ForbiddenError(DomainError):
    status_code = 403
    message = 'Acesso negado'


class TaskNotFoundError(NotFoundError):
    message = 'Task não encontrada'


class UserNotFoundError(NotFoundError):
    message = 'Usuário não encontrado'


class CategoryNotFoundError(NotFoundError):
    message = 'Categoria não encontrada'


class EmailAlreadyUsedError(ConflictError):
    message = 'Email já cadastrado'


class InvalidCredentialsError(UnauthorizedError):
    message = 'Credenciais inválidas'


class InactiveUserError(ForbiddenError):
    message = 'Usuário inativo'
