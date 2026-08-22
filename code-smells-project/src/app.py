"""Composition root: único lugar que constrói dependências concretas e injeta."""
from flask import Flask
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

from src.config.settings import carregar_settings
from src.controllers.health_controller import HealthController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.usuario_controller import UsuarioController
from src.infrastructure.database import Database
from src.infrastructure.logger import configurar_logger
from src.middlewares.error_handler import registrar_error_handlers
from src.models.pedido_model import PedidoRepository
from src.models.produto_model import ProdutoRepository
from src.models.usuario_model import UsuarioRepository
from src.services.health_service import HealthService
from src.services.notification_service import NotificationService
from src.services.pedido_service import PedidoService
from src.services.produto_service import ProdutoService
from src.services.relatorio_service import RelatorioService
from src.services.usuario_service import UsuarioService
from src.views.routes import registrar_rotas


def _verificar_senha(hash_armazenado, senha):
    return check_password_hash(hash_armazenado, senha)


def create_app(settings=None, database=None, logger=None, migrar=True):
    settings = settings or carregar_settings()
    logger = logger or configurar_logger(settings.LOG_LEVEL)
    database = database or Database(settings.DATABASE_PATH)

    if migrar:
        database.migrar(generate_password_hash)

    produto_repository = ProdutoRepository()
    usuario_repository = UsuarioRepository()
    pedido_repository = PedidoRepository()

    notificador = NotificationService(logger)
    produto_service = ProdutoService(database, produto_repository)
    usuario_service = UsuarioService(
        database,
        usuario_repository,
        generate_password_hash,
        _verificar_senha,
        # Custo fixo para o caminho "e-mail inexistente" do login.
        generate_password_hash("hash-descartavel-para-tempo-constante"),
    )
    pedido_service = PedidoService(
        database, pedido_repository, produto_repository, usuario_repository, notificador
    )
    relatorio_service = RelatorioService(database, pedido_repository)
    health_service = HealthService(
        database, produto_repository, usuario_repository, pedido_repository,
        settings.API_VERSION,
    )

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app, origins=settings.CORS_ORIGINS)

    registrar_rotas(app, {
        "produto": ProdutoController(produto_service),
        "usuario": UsuarioController(usuario_service),
        "pedido": PedidoController(pedido_service),
        "relatorio": RelatorioController(relatorio_service),
        "health": HealthController(health_service, settings.API_VERSION),
    })
    registrar_error_handlers(app, logger)

    app.extensions["settings"] = settings
    app.extensions["logger"] = logger
    return app
