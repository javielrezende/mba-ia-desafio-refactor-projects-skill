"""Controllers de Category."""
from flask import jsonify, request

from src.middlewares.pagination import get_pagination, paginated_response


class CategoryController:
    def __init__(self, category_service):
        self._service = category_service

    def list_categories(self):
        limit, offset = get_pagination(request.args)
        items = self._service.list_categories(limit=limit, offset=offset)
        total = len(items) if limit is None else self._service.count_categories()
        return paginated_response(items, total)

    def create_category(self, data, raw_payload, schema):
        return jsonify(self._service.create_category(data)), 201

    def update_category(self, cat_id: int, data, raw_payload, schema):
        return jsonify(self._service.update_category(cat_id, data)), 200

    def delete_category(self, cat_id: int):
        self._service.delete_category(cat_id)
        return jsonify({'message': 'Categoria deletada'}), 200
