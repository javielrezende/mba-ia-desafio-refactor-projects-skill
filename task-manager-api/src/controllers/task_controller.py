"""Controllers de Task: entrada validada → service → resposta HTTP.

Sem SQL, sem regra de negócio e sem try/except — o erro sobe para o error
handler central. Os handlers originais tinham entre 20 e 70 linhas cada.
"""
from flask import jsonify, request

from src.domain.errors import ValidationError
from src.middlewares.pagination import get_pagination, paginated_response


class TaskController:
    def __init__(self, task_service, task_create_schema, task_update_schema):
        self._service = task_service
        self._create_schema = task_create_schema
        self._update_schema = task_update_schema

    def list_tasks(self):
        limit, offset = get_pagination(request.args)
        items = self._service.list_tasks(limit=limit, offset=offset)
        # Sem paginação a lista já é o total: evita uma query de COUNT à toa.
        total = len(items) if limit is None else self._service.count_tasks()
        return paginated_response(items, total)

    def get_task(self, task_id: int):
        return jsonify(self._service.get_task(task_id)), 200

    def create_task(self, data, raw_payload, schema):
        due_date = schema.parse_due_date(data.get('due_date'))
        return jsonify(self._service.create_task(data, due_date)), 201

    def update_task(self, task_id: int, data, raw_payload, schema):
        due_date_provided = 'due_date' in raw_payload
        due_date = schema.parse_due_date(data.get('due_date')) if due_date_provided else None
        return jsonify(self._service.update_task(task_id, data, due_date_provided, due_date)), 200

    def delete_task(self, task_id: int):
        self._service.delete_task(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    def search_tasks(self):
        limit, offset = get_pagination(request.args)
        filters = {
            'term': request.args.get('q', '') or None,
            'status': request.args.get('status', '') or None,
            'priority': _optional_int(request.args.get('priority'), 'priority'),
            'user_id': _optional_int(request.args.get('user_id'), 'user_id'),
        }
        results = self._service.search_tasks(limit=limit, offset=offset, **filters)
        total = len(results) if limit is None else self._service.count_search(**filters)
        return paginated_response(results, total)

    def task_stats(self):
        return jsonify(self._service.stats()), 200


def _optional_int(raw, field: str):
    """Converte parâmetro de query com guarda.

    O código original fazia int(priority) direto: ?priority=alta levantava
    ValueError e devolvia 500 (finding 12 / AP-14).
    """
    if raw is None or raw == '':
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise ValidationError(f'Parâmetro {field} deve ser um número inteiro')
