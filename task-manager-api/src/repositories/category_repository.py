"""Acesso a dados da entidade Category."""
from sqlalchemy import func, select

from src.models.category_model import Category


class CategoryRepository:
    def __init__(self, session):
        self._session = session

    def get(self, category_id: int) -> Category | None:
        return self._session.get(Category, category_id)

    def list_all(self, limit=None, offset=None) -> list[Category]:
        stmt = select(Category).order_by(Category.id)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        return list(self._session.scalars(stmt).all())

    def count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(Category)) or 0

    def add(self, category: Category) -> Category:
        self._session.add(category)
        return category

    def delete(self, category: Category) -> None:
        self._session.delete(category)
