"""Constantes de domínio.

Substitui o bloco de constantes de utils/helpers.py:110-116, que estava definido
e nunca era importado por ninguém, enquanto os literais seguiam espalhados pelos
handlers (finding 14 / AP-16).
"""
from enum import Enum


class Status(str, Enum):
    """Status válidos de uma task."""

    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    DONE = 'done'
    CANCELLED = 'cancelled'


class Role(str, Enum):
    """Papéis válidos de um usuário."""

    USER = 'user'
    ADMIN = 'admin'
    MANAGER = 'manager'


class Priority(int, Enum):
    """Prioridades de uma task, do mais para o menos urgente.

    O significado dos números 1..5 existia apenas implicitamente, no dicionário
    de resposta de /reports/summary. Nomeá-lo aqui torna a semântica explícita
    para todo o código, e é o rótulo usado naquele relatório.
    """

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    MINIMAL = 5

    @property
    def label(self) -> str:
        """Rótulo usado no corpo de /reports/summary (`critical`, `high`, ...)."""
        return self.name.lower()


VALID_STATUSES = [s.value for s in Status]
VALID_ROLES = [r.value for r in Role]

#: Status em que uma task não pode mais ser considerada atrasada.
CLOSED_STATUSES = [Status.DONE.value, Status.CANCELLED.value]

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200

MIN_PRIORITY = Priority.CRITICAL.value
MAX_PRIORITY = Priority.MINIMAL.value
DEFAULT_PRIORITY = Priority.MEDIUM.value

#: Prioridade numérica até a qual uma task é considerada "alta prioridade".
#: Era o literal `if t.priority <= 2` em routes/report_routes.py:129.
HIGH_PRIORITY_THRESHOLD = Priority.HIGH.value

#: Janela do bloco "recent_activity" do relatório resumo.
#: Era `timedelta(days=7)` em routes/report_routes.py:45.
RECENT_ACTIVITY_DAYS = 7

#: Elevado de 4 para 8 — BREAKING CHANGE de segurança (finding 12 / AP-14).
MIN_PASSWORD_LENGTH = 8

DEFAULT_CATEGORY_COLOR = '#000000'

DATE_FORMAT = '%Y-%m-%d'

#: Teto de itens por página quando o cliente pede paginação explicitamente.
MAX_PER_PAGE = 100
DEFAULT_PER_PAGE = 20
