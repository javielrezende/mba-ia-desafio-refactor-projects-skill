"""Acesso a dados da entidade Task.

Recebe a sessão por injeção — nenhum módulo abre a própria conexão (finding 7).
Toda contagem e todo filtro rodam no banco, em vez de carregar a tabela inteira
e percorrer em Python (findings 9 e 11).
"""
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import joinedload

from src.config.constants import CLOSED_STATUSES
from src.models.task_model import Task


class TaskRepository:
    def __init__(self, session):
        self._session = session

    # --- leitura ----------------------------------------------------------

    def get(self, task_id: int) -> Task | None:
        """db.session.get substitui Model.query.get, legado no SQLAlchemy 2.0."""
        return self._session.get(Task, task_id)

    def list_with_relations(self, limit=None, offset=None) -> list[Task]:
        """Lista tasks com user e category carregados na mesma query.

        Antes: 1 + 2N queries, porque o handler fazia User.query.get e
        Category.query.get dentro do laço (finding 9 / AP-11).
        """
        stmt = (
            select(Task)
            .options(joinedload(Task.user), joinedload(Task.category))
            .order_by(Task.id)
        )
        stmt = self._paginate(stmt, limit, offset)
        return list(self._session.scalars(stmt).unique().all())

    def list_all(self, limit=None, offset=None) -> list[Task]:
        stmt = select(Task).order_by(Task.id)
        stmt = self._paginate(stmt, limit, offset)
        return list(self._session.scalars(stmt).all())

    def list_by_user(self, user_id: int, limit=None, offset=None) -> list[Task]:
        stmt = select(Task).where(Task.user_id == user_id).order_by(Task.id)
        stmt = self._paginate(stmt, limit, offset)
        return list(self._session.scalars(stmt).all())

    @staticmethod
    def _search_filters(stmt, term, status, priority, user_id):
        """Filtros de busca, compartilhados pela listagem e pela contagem."""
        if term:
            like = f'%{term}%'
            stmt = stmt.where(or_(Task.title.like(like), Task.description.like(like)))
        if status:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        if user_id is not None:
            stmt = stmt.where(Task.user_id == user_id)
        return stmt

    def search(self, term=None, status=None, priority=None, user_id=None, limit=None, offset=None) -> list[Task]:
        stmt = self._search_filters(select(Task), term, status, priority, user_id)
        stmt = self._paginate(stmt.order_by(Task.id), limit, offset)
        return list(self._session.scalars(stmt).all())

    def count_search(self, term=None, status=None, priority=None, user_id=None) -> int:
        stmt = self._search_filters(
            select(func.count()).select_from(Task), term, status, priority, user_id
        )
        return self._session.scalar(stmt) or 0

    # --- agregação (no banco, não em laço Python) -------------------------

    def count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(Task)) or 0

    def count_by_user(self, user_id: int) -> int:
        return self._session.scalar(
            select(func.count()).select_from(Task).where(Task.user_id == user_id)
        ) or 0

    def count_by_user_map(self) -> dict[int, int]:
        """Total de tasks por usuário, em uma query.

        Substitui o len(u.tasks) dentro do laço de GET /users, que disparava um
        lazy load por usuário (finding 9 / AP-11, routes/user_routes.py:22).
        """
        rows = self._session.execute(
            select(Task.user_id, func.count()).group_by(Task.user_id)
        ).all()
        return {user_id: total for user_id, total in rows if user_id is not None}

    def count_by_status(self) -> dict[str, int]:
        """Uma query com GROUP BY no lugar de um COUNT por status."""
        rows = self._session.execute(select(Task.status, func.count()).group_by(Task.status)).all()
        return {status: total for status, total in rows}

    def count_by_priority(self) -> dict[int, int]:
        rows = self._session.execute(select(Task.priority, func.count()).group_by(Task.priority)).all()
        return {priority: total for priority, total in rows}

    def count_by_category(self) -> dict[int, int]:
        rows = self._session.execute(
            select(Task.category_id, func.count()).group_by(Task.category_id)
        ).all()
        return {category_id: total for category_id, total in rows if category_id is not None}

    def productivity_by_user(self, done_status: str) -> dict[int, dict[str, int]]:
        """Total e concluídas por usuário, em uma query.

        Antes: um filter_by por usuário dentro do laço de User.query.all()
        (finding 9 / AP-11, routes/report_routes.py:56).
        """
        rows = self._session.execute(
            select(
                Task.user_id,
                func.count(),
                func.sum(case((Task.status == done_status, 1), else_=0)),
            ).group_by(Task.user_id)
        ).all()
        return {
            user_id: {'total': total or 0, 'completed': int(completed or 0)}
            for user_id, total, completed in rows
            if user_id is not None
        }

    def list_overdue(self, now) -> list[Task]:
        """Atrasadas resolvidas no WHERE, não filtrando a tabela inteira em memória."""
        stmt = (
            select(Task)
            .where(Task.due_date.isnot(None), Task.due_date < now, Task.status.notin_(CLOSED_STATUSES))
            .order_by(Task.id)
        )
        return list(self._session.scalars(stmt).all())

    def count_overdue(self, now) -> int:
        return self._session.scalar(
            select(func.count())
            .select_from(Task)
            .where(Task.due_date.isnot(None), Task.due_date < now, Task.status.notin_(CLOSED_STATUSES))
        ) or 0

    def count_created_since(self, moment) -> int:
        return self._session.scalar(
            select(func.count()).select_from(Task).where(Task.created_at >= moment)
        ) or 0

    def count_completed_since(self, moment, done_status: str) -> int:
        return self._session.scalar(
            select(func.count())
            .select_from(Task)
            .where(Task.status == done_status, Task.updated_at >= moment)
        ) or 0

    # --- escrita ----------------------------------------------------------

    def add(self, task: Task) -> Task:
        self._session.add(task)
        return task

    def delete(self, task: Task) -> None:
        self._session.delete(task)

    def delete_by_user(self, user_id: int) -> int:
        tasks = self.list_by_user(user_id)
        for task in tasks:
            self._session.delete(task)
        return len(tasks)

    def detach_category(self, category_id: int) -> int:
        """Solta as tasks de uma categoria antes de removê-la.

        Com PRAGMA foreign_keys=ON a exclusão direta falharia; sem ele, deixava
        category_id apontando para uma linha inexistente (finding 8 / AP-09).
        """
        tasks = list(self._session.scalars(select(Task).where(Task.category_id == category_id)).all())
        for task in tasks:
            task.category_id = None
        return len(tasks)

    @staticmethod
    def _paginate(stmt, limit, offset):
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        return stmt
