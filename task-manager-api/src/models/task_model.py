"""Entidade Task e sua serialização."""
from src.config.constants import CLOSED_STATUSES, Status
from src.infrastructure.clock import utc_now
from src.infrastructure.database import db


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=Status.PENDING.value)
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    # --- regra de domínio -------------------------------------------------
    # Estava escrita aqui (models/task.py:50) e nunca era chamada: os 6 pontos
    # que precisavam dela reimplementavam o if aninhado (finding 10 / AP-13).

    def is_overdue(self, now=None) -> bool:
        """A task passou da data limite sem ter sido concluída ou cancelada."""
        if not self.due_date:
            return False
        reference = now or utc_now()
        return self.due_date < reference and self.status not in CLOSED_STATUSES

    def tag_list(self) -> list[str]:
        return self.tags.split(',') if self.tags else []

    # --- serialização -----------------------------------------------------
    # Um serializador por forma de resposta, todos derivados de to_dict().
    # As formas espelham exatamente o contrato que a API já entregava.

    def to_dict(self) -> dict:
        """Forma base — usada por POST, PUT, /tasks/search e dentro de /users/<id>."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tag_list(),
        }

    def to_detail_dict(self, now=None) -> dict:
        """Forma base + `overdue` — usada por GET /tasks/<id>."""
        return {**self.to_dict(), 'overdue': self.is_overdue(now)}

    def to_list_dict(self, now=None) -> dict:
        """Forma detalhada + nomes das relações — usada por GET /tasks.

        Lê self.user / self.category, que são carregados de uma vez pelo
        repositório com joinedload; antes eram duas queries por task
        (finding 9 / AP-11).
        """
        return {
            **self.to_detail_dict(now),
            'user_name': self.user.name if self.user else None,
            'category_name': self.category.name if self.category else None,
        }

    def to_brief_dict(self, now=None) -> dict:
        """Forma reduzida — usada por GET /users/<id>/tasks."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(now),
        }
