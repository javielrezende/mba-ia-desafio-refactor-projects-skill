"""Regra de negócio dos relatórios.

Era o handler de 90 linhas de routes/report_routes.py:12-101, que fazia 11
queries diretas, um filter_by por usuário dentro do laço e carregava a tabela
inteira de tasks em memória para contar atrasadas (findings 4, 5 e 9).
"""
from datetime import timedelta

from src.config.constants import HIGH_PRIORITY_THRESHOLD, Priority, RECENT_ACTIVITY_DAYS, Status


class ReportService:
    def __init__(self, task_repository, user_repository, category_repository, clock, task_service):
        self._tasks = task_repository
        self._users = user_repository
        self._categories = category_repository
        self._clock = clock
        self._task_service = task_service

    def summary(self) -> dict:
        now = self._clock()
        by_status = self._tasks.count_by_status()
        by_priority = self._tasks.count_by_priority()
        overdue_tasks = self._tasks.list_overdue(now)
        recent_window = now - timedelta(days=RECENT_ACTIVITY_DAYS)

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': self._tasks.count(),
                'total_users': self._users.count(),
                'total_categories': self._categories.count(),
            },
            'tasks_by_status': {
                'pending': by_status.get(Status.PENDING.value, 0),
                'in_progress': by_status.get(Status.IN_PROGRESS.value, 0),
                'done': by_status.get(Status.DONE.value, 0),
                'cancelled': by_status.get(Status.CANCELLED.value, 0),
            },
            # Os rótulos vêm do próprio Enum: a semântica de 1..5 não é mais
            # um literal solto aqui (finding 14 / AP-16).
            'tasks_by_priority': {
                priority.label: by_priority.get(priority.value, 0) for priority in Priority
            },
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': [
                    {
                        'id': task.id,
                        'title': task.title,
                        'due_date': str(task.due_date),
                        'days_overdue': (now - task.due_date).days,
                    }
                    for task in overdue_tasks
                ],
            },
            'recent_activity': {
                'tasks_created_last_7_days': self._tasks.count_created_since(recent_window),
                'tasks_completed_last_7_days': self._tasks.count_completed_since(
                    recent_window, Status.DONE.value
                ),
            },
            'user_productivity': self._user_productivity(),
        }

    def _user_productivity(self) -> list[dict]:
        """Uma query de agregação no lugar de um filter_by por usuário."""
        users = self._users.list_all()
        productivity = self._tasks.productivity_by_user(Status.DONE.value)
        result = []
        for user in users:
            stats = productivity.get(user.id, {'total': 0, 'completed': 0})
            total, completed = stats['total'], stats['completed']
            result.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': self._task_service.completion_rate(completed, total),
            })
        return result

    def user_report(self, user_id: int) -> dict:
        from src.domain.errors import UserNotFoundError

        user = self._users.get(user_id)
        if not user:
            raise UserNotFoundError()

        now = self._clock()
        tasks = self._tasks.list_by_user(user_id)

        counts = {status.value: 0 for status in Status}
        overdue = 0
        high_priority = 0
        for task in tasks:
            if task.status in counts:
                counts[task.status] += 1
            if task.priority <= HIGH_PRIORITY_THRESHOLD:
                high_priority += 1
            if task.is_overdue(now):
                overdue += 1

        total = len(tasks)
        done = counts[Status.DONE.value]
        return {
            'user': user.to_summary_dict(),
            'statistics': {
                'total_tasks': total,
                'done': done,
                'pending': counts[Status.PENDING.value],
                'in_progress': counts[Status.IN_PROGRESS.value],
                'cancelled': counts[Status.CANCELLED.value],
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': self._task_service.completion_rate(done, total),
            },
        }
