"""Mapeamento rota → controller.

Uma linha por endpoint, mais os middlewares de autenticação e de validação.
Nenhuma regra de negócio, nenhum SQL, nenhum try/except.

Os blueprints reproduzem exatamente os 22 endpoints originais. `categories` saiu
do blueprint de relatórios, onde não tinha relação nenhuma com o domínio
(finding 4 / AP-03).

Autenticação: **toda rota exige `Authorization: Bearer <token>`**, exceto as
quatro listadas em `PUBLIC_ROUTES` abaixo. Não há flag que desligue isso — ver
o cabeçalho de middlewares/auth.py e a seção *Breaking changes* do relatório.
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

#: As únicas rotas que respondem sem credencial, e o motivo de cada uma.
#: Qualquer acréscimo aqui é uma decisão de segurança e vai justificada no
#: relatório de auditoria, rota por rota.
PUBLIC_ROUTES = {
    'POST /login': 'emite o token — exigir token seria impossível',
    'POST /users': 'registro de conta; definir papel privilegiado segue exigindo admin',
    'GET /': 'liveness probe, sem dado de negócio',
    'GET /health': 'liveness probe, sem dado de negócio',
}


def build_blueprints(controllers) -> list[Blueprint]:
    tasks = controllers['task']
    users = controllers['user']
    categories = controllers['category']
    reports = controllers['report']
    health = controllers['health']

    #: No registro, o papel padrão `user` continua liberado; qualquer papel
    #: privilegiado exige um admin autenticado.
    role_on_create = require_admin_for_role(allow_default=True)
    role_on_update = require_admin_for_role(allow_default=False)
    self_or_admin = require_self_or_admin()

    # --- público: liveness -------------------------------------------------
    root_bp = Blueprint('root', __name__)
    root_bp.add_url_rule('/', view_func=health.index, methods=['GET'])
    root_bp.add_url_rule('/health', view_func=health.health, methods=['GET'])

    # --- tasks: tudo autenticado ------------------------------------------
    task_bp = Blueprint('tasks', __name__)
    task_bp.add_url_rule('/tasks', 'list_tasks', require_auth(tasks.list_tasks), methods=['GET'])
    task_bp.add_url_rule(
        '/tasks/search', 'search_tasks', require_auth(tasks.search_tasks), methods=['GET']
    )
    task_bp.add_url_rule(
        '/tasks/stats', 'task_stats', require_auth(tasks.task_stats), methods=['GET']
    )
    task_bp.add_url_rule(
        '/tasks/<int:task_id>', 'get_task', require_auth(tasks.get_task), methods=['GET']
    )
    task_bp.add_url_rule(
        '/tasks',
        'create_task',
        require_auth(validate_body(TaskCreateSchema, TASK_ERROR_ORDER)(tasks.create_task)),
        methods=['POST'],
    )
    task_bp.add_url_rule(
        '/tasks/<int:task_id>',
        'update_task',
        require_auth(validate_body(TaskUpdateSchema, TASK_ERROR_ORDER)(tasks.update_task)),
        methods=['PUT'],
    )
    task_bp.add_url_rule(
        '/tasks/<int:task_id>', 'delete_task', require_auth(tasks.delete_task), methods=['DELETE']
    )

    # --- users: leitura autenticada; escrita com dono/admin ---------------
    user_bp = Blueprint('users', __name__)
    user_bp.add_url_rule('/users', 'list_users', require_auth(users.list_users), methods=['GET'])
    user_bp.add_url_rule(
        '/users/<int:user_id>', 'get_user', require_auth(users.get_user), methods=['GET']
    )
    user_bp.add_url_rule(
        '/users/<int:user_id>/tasks',
        'get_user_tasks',
        require_auth(users.get_user_tasks),
        methods=['GET'],
    )
    # Pública: sem ela não existe a primeira conta. `role_on_create` mantém o
    # registro restrito ao papel padrão `user`.
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
    user_bp.add_url_rule(
        '/users/<int:user_id>', 'delete_user', require_admin(users.delete_user), methods=['DELETE']
    )
    # Pública: é a rota que emite o token.
    user_bp.add_url_rule(
        '/login',
        'login',
        validate_body(LoginSchema, LOGIN_ERROR_ORDER)(users.login),
        methods=['POST'],
    )

    # --- categories: tudo autenticado -------------------------------------
    category_bp = Blueprint('categories', __name__)
    category_bp.add_url_rule(
        '/categories',
        'list_categories',
        require_auth(categories.list_categories),
        methods=['GET'],
    )
    category_bp.add_url_rule(
        '/categories',
        'create_category',
        require_auth(
            validate_body(CategoryCreateSchema, CATEGORY_ERROR_ORDER)(categories.create_category)
        ),
        methods=['POST'],
    )
    category_bp.add_url_rule(
        '/categories/<int:cat_id>',
        'update_category',
        require_auth(
            validate_body(
                CategoryUpdateSchema, CATEGORY_ERROR_ORDER, reject_empty=False
            )(categories.update_category)
        ),
        methods=['PUT'],
    )
    category_bp.add_url_rule(
        '/categories/<int:cat_id>',
        'delete_category',
        require_auth(categories.delete_category),
        methods=['DELETE'],
    )

    # --- reports: tudo autenticado ----------------------------------------
    report_bp = Blueprint('reports', __name__)
    report_bp.add_url_rule(
        '/reports/summary', 'summary_report', require_auth(reports.summary_report), methods=['GET']
    )
    report_bp.add_url_rule(
        '/reports/user/<int:user_id>',
        'user_report',
        require_auth(reports.user_report),
        methods=['GET'],
    )

    return [root_bp, task_bp, user_bp, category_bp, report_bp]
