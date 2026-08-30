"""Composition root: monta as dependências e devolve a aplicação Flask.

É o único lugar do projeto que constrói objetos concretos (sessão de banco,
logger, notificador). Nenhum model, service ou controller instancia a própria
conexão — todos recebem o que precisam por injeção (finding 7 / AP-07).

Como é um application factory, o teste pode montar a aplicação com dependências
falsas: create_app(settings_override=..., session=...).
"""
from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings, settings as default_settings
from src.infrastructure.clock import utc_now
from src.infrastructure.database import db
from src.infrastructure.logger import configure_logging
from src.controllers.category_controller import CategoryController
from src.controllers.health_controller import HealthController
from src.controllers.report_controller import ReportController
from src.controllers.task_controller import TaskController
from src.controllers.user_controller import UserController
from src.middlewares.error_handler import register_error_handlers
from src.middlewares.pagination import TOTAL_COUNT_HEADER
from src.repositories.category_repository import CategoryRepository
from src.repositories.task_repository import TaskRepository
from src.repositories.user_repository import UserRepository
from src.schemas.task_schema import TaskCreateSchema, TaskUpdateSchema
from src.services.category_service import CategoryService
from src.services.notification_service import NotificationService
from src.services.report_service import ReportService
from src.services.task_service import TaskService
from src.services.user_service import UserService
from src.views.routes import build_blueprints

# Importar o pacote de models registra as três entidades no metadata do
# SQLAlchemy antes do create_all().
import src.models  # noqa: F401


def create_app(settings: Settings | None = None, clock=utc_now, notifier=None) -> Flask:
    settings = settings or default_settings
    logger = configure_logging()

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = settings.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['DEBUG'] = settings.DEBUG

    # CORS restrito às origens configuradas, em vez de liberar todas.
    # expose_headers é necessário para que o JS no navegador consiga ler o
    # X-Total-Count — headers customizados ficam ocultos por padrão.
    CORS(app, origins=settings.CORS_ORIGINS, expose_headers=[TOTAL_COUNT_HEADER])
    db.init_app(app)

    session = db.session
    task_repository = TaskRepository(session)
    user_repository = UserRepository(session)
    category_repository = CategoryRepository(session)

    notifier = notifier or NotificationService(settings, logger)

    task_service = TaskService(
        task_repository, user_repository, category_repository, session, clock, logger, notifier
    )
    user_service = UserService(user_repository, task_repository, session, logger, notifier)
    category_service = CategoryService(category_repository, task_repository, session, logger)
    report_service = ReportService(
        task_repository, user_repository, category_repository, clock, task_service
    )

    controllers = {
        'task': TaskController(task_service, TaskCreateSchema, TaskUpdateSchema),
        'user': UserController(user_service, task_service),
        'category': CategoryController(category_service),
        'report': ReportController(report_service),
        'health': HealthController(),
    }

    for blueprint in build_blueprints(controllers):
        app.register_blueprint(blueprint)

    register_error_handlers(app, logger)

    with app.app_context():
        db.create_all()

    logger.info('aplicação montada env=%s debug=%s', settings.ENV, settings.DEBUG)
    return app
