"""Entidade User e sua serialização."""
from src.config.constants import Role
from src.infrastructure.clock import utc_now
from src.infrastructure.database import db
from src.infrastructure.security import hash_password, verify_password


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=Role.USER.value)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def set_password(self, raw_password: str) -> None:
        """Grava o hash salgado da senha. Antes era MD5 sem salt (finding 2)."""
        self.password = hash_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return verify_password(self.password, raw_password)

    def is_admin(self) -> bool:
        """Usado pelo middleware de autorização (src/middlewares/auth.py)."""
        return self.role == Role.ADMIN.value

    def to_dict(self) -> dict:
        """Serialização única do usuário.

        BREAKING CHANGE de segurança: o campo 'password' (que era o hash) saiu
        daqui. Ele vazava por GET /users/<id>, POST /users, PUT /users/<id> e
        pelo corpo do login (finding 1 / AP-05).
        """
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def to_summary_dict(self) -> dict:
        """Identificação mínima — usada no cabeçalho de /reports/user/<id>."""
        return {'id': self.id, 'name': self.name, 'email': self.email}
