"""Regra de negócio de User, incluindo autenticação."""
from src.domain.errors import (
    EmailAlreadyUsedError,
    InactiveUserError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from src.infrastructure.security import DUMMY_PASSWORD_HASH, issue_token, verify_password
from src.models.user_model import User


class UserService:
    def __init__(self, user_repository, task_repository, session, logger, notifier=None):
        self._users = user_repository
        self._tasks = task_repository
        self._session = session
        self._logger = logger
        self._notifier = notifier

    # --- leitura ----------------------------------------------------------

    def list_users(self, limit=None, offset=None) -> list[dict]:
        """Lista com task_count resolvido por GROUP BY, não por lazy load por usuário."""
        users = self._users.list_all(limit=limit, offset=offset)
        counts = self._tasks.count_by_user_map()
        return [{**user.to_dict(), 'task_count': counts.get(user.id, 0)} for user in users]

    def count_users(self) -> int:
        return self._users.count()

    def get_user_with_tasks(self, user_id: int) -> dict:
        user = self._require_user(user_id)
        tasks = self._tasks.list_by_user(user_id)
        return {**user.to_dict(), 'tasks': [task.to_dict() for task in tasks]}

    # --- escrita ----------------------------------------------------------

    def create_user(self, data: dict) -> dict:
        if self._users.find_by_email(data['email']):
            raise EmailAlreadyUsedError()

        user = User()
        user.name = data['name']
        user.email = data['email']
        user.set_password(data['password'])
        user.role = data['role']

        with self._session.begin_nested():
            self._users.add(user)
        self._session.commit()

        self._logger.info('usuário criado id=%s role=%s', user.id, user.role)
        return user.to_dict()

    def update_user(self, user_id: int, data: dict) -> dict:
        user = self._require_user(user_id)

        if 'email' in data:
            existing = self._users.find_by_email(data['email'])
            if existing and existing.id != user_id:
                raise EmailAlreadyUsedError()
            user.email = data['email']
        if 'name' in data:
            user.name = data['name']
        if 'password' in data:
            user.set_password(data['password'])
        if 'role' in data:
            user.role = data['role']
        if 'active' in data:
            user.active = data['active']

        self._session.commit()
        self._logger.info('usuário atualizado id=%s', user.id)
        return user.to_dict()

    def delete_user(self, user_id: int) -> None:
        """Remove o usuário e suas tasks numa única transação.

        Antes o laço de exclusão das tasks rodava fora do try que protegia o
        commit, deixando a sessão suja em caso de falha (finding 8 / AP-09).
        """
        user = self._require_user(user_id)
        with self._session.begin_nested():
            removed = self._tasks.delete_by_user(user_id)
            self._users.delete(user)
        self._session.commit()
        self._logger.info('usuário deletado id=%s tasks_removidas=%s', user_id, removed)

    # --- autenticação -----------------------------------------------------

    def authenticate(self, email: str, raw_password: str) -> dict:
        """Autentica sem vazar quais e-mails existem.

        O hash é sempre calculado — contra o hash real ou contra um dummy de
        mesmo custo — para que o tempo de resposta não denuncie a existência da
        conta (finding 2 / AP-04).
        """
        user = self._users.find_by_email(email)
        stored_hash = user.password if user else DUMMY_PASSWORD_HASH
        password_ok = verify_password(stored_hash, raw_password)

        if not user or not password_ok:
            raise InvalidCredentialsError()
        if not user.active:
            raise InactiveUserError()

        self._logger.info('login realizado id=%s', user.id)
        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': issue_token(user.id, user.role),
        }

    # --- apoio ------------------------------------------------------------

    def _require_user(self, user_id: int) -> User:
        user = self._users.get(user_id)
        if not user:
            raise UserNotFoundError()
        return user
