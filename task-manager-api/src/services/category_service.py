"""Regra de negócio de Category."""
from src.domain.errors import CategoryNotFoundError
from src.models.category_model import Category


class CategoryService:
    def __init__(self, category_repository, task_repository, session, logger):
        self._categories = category_repository
        self._tasks = task_repository
        self._session = session
        self._logger = logger

    def list_categories(self, limit=None, offset=None) -> list[dict]:
        """task_count vem de um GROUP BY, não de um COUNT por categoria."""
        categories = self._categories.list_all(limit=limit, offset=offset)
        counts = self._tasks.count_by_category()
        return [{**c.to_dict(), 'task_count': counts.get(c.id, 0)} for c in categories]

    def count_categories(self) -> int:
        return self._categories.count()

    def create_category(self, data: dict) -> dict:
        category = Category()
        category.name = data['name']
        category.description = data.get('description', '')
        category.color = data.get('color')

        with self._session.begin_nested():
            self._categories.add(category)
        self._session.commit()

        self._logger.info('categoria criada id=%s', category.id)
        return category.to_dict()

    def update_category(self, category_id: int, data: dict) -> dict:
        category = self._require_category(category_id)
        for field in ('name', 'description', 'color'):
            if field in data:
                setattr(category, field, data[field])
        self._session.commit()
        return category.to_dict()

    def delete_category(self, category_id: int) -> None:
        """Solta as tasks da categoria antes de removê-la, na mesma transação.

        Antes, a categoria era apagada e as tasks ficavam com category_id
        apontando para uma linha inexistente (finding 8 / AP-09). Com
        PRAGMA foreign_keys=ON ativo, a exclusão direta agora falharia.
        """
        category = self._require_category(category_id)
        with self._session.begin_nested():
            detached = self._tasks.detach_category(category_id)
            self._categories.delete(category)
        self._session.commit()
        self._logger.info('categoria deletada id=%s tasks_desvinculadas=%s', category_id, detached)

    def _require_category(self, category_id: int) -> Category:
        category = self._categories.get(category_id)
        if not category:
            raise CategoryNotFoundError()
        return category
