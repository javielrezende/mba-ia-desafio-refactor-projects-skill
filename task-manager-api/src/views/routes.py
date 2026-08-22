"""Mapeamento rota → controller.

Uma linha por endpoint, mais o middleware de validação nas rotas de escrita.
Nenhuma regra de negócio, nenhum SQL, nenhum try/except.

Os blueprints reproduzem exatamente os 22 endpoints originais. `categories` saiu
do blueprint de relatórios, onde não tinha relação nenhuma com o domínio
(finding 4 / AP-03).
"""
from flask import Blueprint

from src.middlewares.auth import (
    require_admin,
    require_admin_for_role,
    require_auth,
    require_self_or_admin,
)
from src.middlewares.validation import validate_body
from src.schemas.category_schema import (
    CATEGORY_ERROR_ORDER,
    CategoryCreateSchema,
    CategoryUpdateSchema,
)
from src.schemas.task_schema import TASK_ERROR_ORDER, TaskCreateSchema, TaskUpdateSchema
from src.schemas.user_schema import (
    LOGIN_ERROR_ORDER,
    USER_ERROR_ORDER,
    LoginSchema,
    UserCreateSchema,
    UserUpdateSchema,
)


def build_blueprints(controllers, settings) -> list[Blueprint]:
    tasks = controllers['task']
    users = controllers['user']
    categories = controllers['category']
    reports = controllers['report']
    health = controllers['health']

    auth = require_auth(settings)
    admin = require_admin(settings)
    self_or_admin = require_self_or_admin(settings)
    #: No registro, o papel padrão `user` continua liberado; qualquer papel
    #: privilegiado exige um admin autenticado.
    role_on_create = require_admin_for_role(settings, allow_default=True)
    role_on_update = require_admin_for_role(settings, allow_default=False)

    root_bp = Blueprint('root', __name__)
    root_bp.add_url_rule('/', view_func=health.index, methods=['GET'])
    root_bp.add_url_rule('/health', view_func=health.health, methods=['GET'])

    task_bp = Blueprint('tasks', __name__)
    task_bp.add_url_rule('/tasks', 'list_tasks', tasks.list_tasks, methods=['GET'])
    task_bp.add_url_rule('/tasks/search', 'search_tasks', tasks.search_tasks, methods=['GET'])
    task_bp.add_url_rule('/tasks/stats', 'task_stats', tasks.task_stats, methods=['GET'])
    task_bp.add_url_rule('/tasks/<int:task_id>', 'get_task', tasks.get_task, methods=['GET'])
    task_bp.add_url_rule(
        '/tasks',
        'create_task',
        auth(validate_body(TaskCreateSchema, TASK_ERROR_ORDER)(tasks.create_task)),
        methods=['POST'],
    )
    task_bp.add_url_rule(
        '/tasks/<int:task_id>',
        'update_task',
        auth(validate_body(TaskUpdateSchema, TASK_ERROR_ORDER)(tasks.update_task)),
        methods=['PUT'],
    )
    task_bp.add_url_rule('/tasks/<int:task_id>', 'delete_task', auth(tasks.delete_task), methods=['DELETE'])

    user_bp = Blueprint('users', __name__)
    user_bp.add_url_rule('/users', 'list_users', users.list_users, methods=['GET'])
    user_bp.add_url_rule('/users/<int:user_id>', 'get_user', users.get_user, methods=['GET'])
    user_bp.add_url_rule('/users/<int:user_id>/tasks', 'get_user_tasks', users.get_user_tasks, methods=['GET'])
    user_bp.add_url_rule(
        '/users',
        'create_user',
        role_on_create(validate_body(UserCreateSchema, USER_ERROR_ORDER)(users.create_user)),
        methods=['POST'],
    )
    user_bp.add_url_rule(
        '/users/<int:user_id>',
        'update_user',
        self_or_admin(
            role_on_update(validate_body(UserUpdateSchema, USER_ERROR_ORDER)(users.update_user))
        ),
        methods=['PUT'],
    )
    user_bp.add_url_rule('/users/<int:user_id>', 'delete_user', admin(users.delete_user), methods=['DELETE'])
    user_bp.add_url_rule(
        '/login',
        'login',
        validate_body(LoginSchema, LOGIN_ERROR_ORDER)(users.login),
        methods=['POST'],
    )

    category_bp = Blueprint('categories', __name__)
    category_bp.add_url_rule('/categories', 'list_categories', categories.list_categories, methods=['GET'])
    category_bp.add_url_rule(
        '/categories',
        'create_category',
        auth(validate_body(CategoryCreateSchema, CATEGORY_ERROR_ORDER)(categories.create_category)),
        methods=['POST'],
    )
    category_bp.add_url_rule(
        '/categories/<int:cat_id>',
        'update_category',
        auth(
            validate_body(
                CategoryUpdateSchema, CATEGORY_ERROR_ORDER, reject_empty=False
            )(categories.update_category)
        ),
        methods=['PUT'],
    )
    category_bp.add_url_rule(
        '/categories/<int:cat_id>', 'delete_category', auth(categories.delete_category), methods=['DELETE']
    )

    report_bp = Blueprint('reports', __name__)
    report_bp.add_url_rule('/reports/summary', 'summary_report', reports.summary_report, methods=['GET'])
    report_bp.add_url_rule('/reports/user/<int:user_id>', 'user_report', reports.user_report, methods=['GET'])

    return [root_bp, task_bp, user_bp, category_bp, report_bp]
