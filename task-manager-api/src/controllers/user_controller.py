"""Controllers de User."""
from flask import jsonify, request

from src.middlewares.pagination import get_pagination, paginated_response


class UserController:
    def __init__(self, user_service, task_service):
        self._users = user_service
        self._tasks = task_service

    def list_users(self):
        limit, offset = get_pagination(request.args)
        items = self._users.list_users(limit=limit, offset=offset)
        total = len(items) if limit is None else self._users.count_users()
        return paginated_response(items, total)

    def get_user(self, user_id: int):
        return jsonify(self._users.get_user_with_tasks(user_id)), 200

    def create_user(self, data, raw_payload, schema):
        return jsonify(self._users.create_user(data)), 201

    def update_user(self, user_id: int, data, raw_payload, schema):
        return jsonify(self._users.update_user(user_id, data)), 200

    def delete_user(self, user_id: int):
        self._users.delete_user(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    def get_user_tasks(self, user_id: int):
        limit, offset = get_pagination(request.args)
        items = self._tasks.list_user_tasks(user_id, limit=limit, offset=offset)
        total = len(items) if limit is None else self._tasks.count_user_tasks(user_id)
        return paginated_response(items, total)

    def login(self, data, raw_payload, schema):
        return jsonify(self._users.authenticate(data['email'], data['password'])), 200
