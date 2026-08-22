"""Acesso a dados da entidade User."""
from sqlalchemy import func, select

from src.models.user_model import User


class UserRepository:
    def __init__(self, session):
        self._session = session

    def get(self, user_id: int) -> User | None:
        return self._session.get(User, user_id)

    def find_by_email(self, email: str) -> User | None:
        return self._session.scalars(select(User).where(User.email == email)).first()

    def list_all(self, limit=None, offset=None) -> list[User]:
        stmt = select(User).order_by(User.id)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        return list(self._session.scalars(stmt).all())

    def count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(User)) or 0

    def add(self, user: User) -> User:
        self._session.add(user)
        return user

    def delete(self, user: User) -> None:
        self._session.delete(user)
