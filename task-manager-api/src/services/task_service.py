"""Regra de negócio de Task.

Não conhece HTTP: recebe dados já validados, devolve entidades ou dicionários e
lança exceções de domínio. Antes, tudo isto vivia dentro dos handlers de
routes/task_routes.py (finding 5 / AP-06).
"""
from src.config.constants import Status
from src.domain.errors import CategoryNotFoundError, TaskNotFoundError, UserNotFoundError
from src.models.task_model import Task


class TaskService:
    def __init__(self, task_repository, user_repository, category_repository, session, clock, logger, notifier=None):
        self._tasks = task_repository
        self._users = user_repository
        self._categories = category_repository
        self._session = session
        self._clock = clock
        self._logger = logger
        self._notifier = notifier

    # --- leitura ----------------------------------------------------------

    def list_tasks(self, limit=None, offset=None) -> list[dict]:
        now = self._clock()
        tasks = self._tasks.list_with_relations(limit=limit, offset=offset)
        return [task.to_list_dict(now) for task in tasks]

    def count_tasks(self) -> int:
        return self._tasks.count()

    def count_search(self, term=None, status=None, priority=None, user_id=None) -> int:
        return self._tasks.count_search(term=term, status=status, priority=priority, user_id=user_id)

    def count_user_tasks(self, user_id: int) -> int:
        return self._tasks.count_by_user(user_id)

    def get_task(self, task_id: int) -> dict:
        task = self._require_task(task_id)
        return task.to_detail_dict(self._clock())

    def search_tasks(self, term=None, status=None, priority=None, user_id=None, limit=None, offset=None) -> list[dict]:
        tasks = self._tasks.search(
            term=term, status=status, priority=priority, user_id=user_id, limit=limit, offset=offset
        )
        return [task.to_dict() for task in tasks]

    def list_user_tasks(self, user_id: int, limit=None, offset=None) -> list[dict]:
        self._require_user(user_id)
        now = self._clock()
        tasks = self._tasks.list_by_user(user_id, limit=limit, offset=offset)
        return [task.to_brief_dict(now) for task in tasks]

    def stats(self) -> dict:
        """Contagens agregadas no banco, não percorrendo a tabela em Python."""
        by_status = self._tasks.count_by_status()
        total = self._tasks.count()
        done = by_status.get(Status.DONE.value, 0)
        return {
            'total': total,
            'pending': by_status.get(Status.PENDING.value, 0),
            'in_progress': by_status.get(Status.IN_PROGRESS.value, 0),
            'done': done,
            'cancelled': by_status.get(Status.CANCELLED.value, 0),
            'overdue': self._tasks.count_overdue(self._clock()),
            'completion_rate': self.completion_rate(done, total),
        }

    @staticmethod
    def completion_rate(done: int, total: int) -> float:
        """Regra única de taxa de conclusão — estava reescrita em 3 pontos."""
        return round((done / total) * 100, 2) if total > 0 else 0

    # --- escrita ----------------------------------------------------------

    def create_task(self, data: dict, due_date) -> dict:
        self._validate_relations(data.get('user_id'), data.get('category_id'))

        task = Task()
        task.title = data['title']
        task.description = data.get('description', '')
        task.status = data.get('status', Status.PENDING.value)
        task.priority = data.get('priority')
        task.user_id = data.get('user_id')
        task.category_id = data.get('category_id')
        task.due_date = due_date
        task.tags = data.get('tags')

        with self._session.begin_nested():
            self._tasks.add(task)
        self._session.commit()

        self._logger.info('task criada id=%s title=%s', task.id, task.title)
        self._notify_assignment(task)
        return task.to_dict()

    def update_task(self, task_id: int, data: dict, due_date_provided: bool, due_date) -> dict:
        task = self._require_task(task_id)
        self._validate_relations(
            data.get('user_id') if 'user_id' in data else None,
            data.get('category_id') if 'category_id' in data else None,
        )

        for field in ('title', 'description', 'status', 'priority', 'user_id', 'category_id', 'tags'):
            if field in data:
                setattr(task, field, data[field])
        if due_date_provided:
            task.due_date = due_date
        task.updated_at = self._clock()

        self._session.commit()
        self._logger.info('task atualizada id=%s', task.id)
        return task.to_dict()

    def delete_task(self, task_id: int) -> None:
        task = self._require_task(task_id)
        with self._session.begin_nested():
            self._tasks.delete(task)
        self._session.commit()
        self._logger.info('task deletada id=%s', task_id)

    # --- apoio ------------------------------------------------------------

    def _notify_assignment(self, task: Task) -> None:
        """Avisa o responsável pela task, se houver um e um notificador injetado.

        É o ponto que liga services/notification_service.py ao fluxo — o módulo
        original não era importado por ninguém (finding 16 / AP-19).
        """
        if not self._notifier or not task.user_id:
            return
        user = self._users.get(task.user_id)
        if user:
            self._notifier.notify_task_assigned(user, task)

    def _require_task(self, task_id: int) -> Task:
        task = self._tasks.get(task_id)
        if not task:
            raise TaskNotFoundError()
        return task

    def _require_user(self, user_id: int):
        user = self._users.get(user_id)
        if not user:
            raise UserNotFoundError()
        return user

    def _validate_relations(self, user_id, category_id) -> None:
        """Usuário e categoria inexistentes devolviam 404 no código original."""
        if user_id and not self._users.get(user_id):
            raise UserNotFoundError()
        if category_id and not self._categories.get(category_id):
            raise CategoryNotFoundError()
