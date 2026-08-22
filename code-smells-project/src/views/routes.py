"""Mapeamento rota -> controller. Nenhuma regra, nenhum SQL, nenhum try/except."""
from flask import Blueprint

from src.middlewares.validation import validar_corpo
from src.schemas.pedido_schema import pedido_schema, status_pedido_schema
from src.schemas.produto_schema import produto_schema
from src.schemas.usuario_schema import login_schema, usuario_schema


def registrar_rotas(app, controllers):
    produtos = controllers["produto"]
    usuarios = controllers["usuario"]
    pedidos = controllers["pedido"]
    relatorios = controllers["relatorio"]
    health = controllers["health"]

    api = Blueprint("api", __name__)

    api.add_url_rule("/", "index", health.index, methods=["GET"])
    api.add_url_rule("/health", "health_check", health.health, methods=["GET"])

    api.add_url_rule("/produtos", "listar_produtos", produtos.listar, methods=["GET"])
    api.add_url_rule("/produtos/busca", "buscar_produtos", produtos.pesquisar, methods=["GET"])
    api.add_url_rule("/produtos/<int:id>", "buscar_produto", produtos.buscar, methods=["GET"])
    api.add_url_rule("/produtos", "criar_produto",
                     validar_corpo(produto_schema)(produtos.criar), methods=["POST"])
    # O PUT valida dentro do service: o contrato exige 404 de produto inexistente
    # ANTES de qualquer erro de validação de corpo.
    api.add_url_rule("/produtos/<int:id>", "atualizar_produto", produtos.atualizar,
                     methods=["PUT"])
    api.add_url_rule("/produtos/<int:id>", "deletar_produto", produtos.deletar,
                     methods=["DELETE"])

    api.add_url_rule("/usuarios", "listar_usuarios", usuarios.listar, methods=["GET"])
    api.add_url_rule("/usuarios/<int:id>", "buscar_usuario", usuarios.buscar, methods=["GET"])
    api.add_url_rule("/usuarios", "criar_usuario",
                     validar_corpo(usuario_schema)(usuarios.criar), methods=["POST"])
    api.add_url_rule("/login", "login",
                     validar_corpo(login_schema)(usuarios.login), methods=["POST"])

    api.add_url_rule("/pedidos", "criar_pedido",
                     validar_corpo(pedido_schema)(pedidos.criar), methods=["POST"])
    api.add_url_rule("/pedidos", "listar_todos_pedidos", pedidos.listar, methods=["GET"])
    api.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
                     pedidos.listar_por_usuario, methods=["GET"])
    api.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
                     validar_corpo(status_pedido_schema)(pedidos.atualizar_status),
                     methods=["PUT"])

    api.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorios.vendas,
                     methods=["GET"])

    app.register_blueprint(api)
