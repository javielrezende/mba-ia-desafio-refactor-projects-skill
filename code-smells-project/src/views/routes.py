"""Mapeamento rota -> controller. Nenhuma regra, nenhum SQL, nenhum try/except.

Cada linha carrega o gate de acesso da rota (`middlewares/auth.py`) e, quando é
escrita, o middleware de validação. **Deny-by-default:** toda rota exige
`Authorization: Bearer <token>`, exceto as quatro de `ROTAS_PUBLICAS`.
"""
from flask import Blueprint

from src.middlewares.auth import (
    exigir_admin,
    exigir_autenticacao,
    exigir_dono_no_corpo,
    exigir_dono_ou_admin,
)
from src.middlewares.validation import validar_corpo
from src.schemas.pedido_schema import pedido_schema, status_pedido_schema
from src.schemas.produto_schema import produto_schema
from src.schemas.usuario_schema import login_schema, usuario_schema

#: As únicas rotas que respondem sem credencial, e o motivo de cada uma.
#: Acrescentar uma linha aqui é decisão de segurança e vai justificada no
#: relatório de auditoria, rota por rota. Relatório, faturamento, listagem de
#: usuários, listagem global e escrita nunca entram nesta lista.
ROTAS_PUBLICAS = {
    "POST /login": "emite o token — exigir token aqui seria impossível",
    "POST /usuarios": "registro de conta; o papel é sempre 'cliente', nunca vem do corpo",
    "GET /": "liveness probe, sem dado de negócio",
    "GET /health": "liveness probe, sem dado de negócio",
}


def registrar_rotas(app, controllers):
    produtos = controllers["produto"]
    usuarios = controllers["usuario"]
    pedidos = controllers["pedido"]
    relatorios = controllers["relatorio"]
    health = controllers["health"]

    api = Blueprint("api", __name__)

    # --- público: liveness -------------------------------------------------
    api.add_url_rule("/", "index", health.index, methods=["GET"])
    api.add_url_rule("/health", "health_check", health.health, methods=["GET"])

    # --- produtos: leitura autenticada, escrita de catálogo só admin -------
    api.add_url_rule("/produtos", "listar_produtos",
                     exigir_autenticacao(produtos.listar), methods=["GET"])
    api.add_url_rule("/produtos/busca", "buscar_produtos",
                     exigir_autenticacao(produtos.pesquisar), methods=["GET"])
    api.add_url_rule("/produtos/<int:id>", "buscar_produto",
                     exigir_autenticacao(produtos.buscar), methods=["GET"])
    api.add_url_rule("/produtos", "criar_produto",
                     exigir_admin(validar_corpo(produto_schema)(produtos.criar)),
                     methods=["POST"])
    # O PUT valida dentro do service: o contrato exige 404 de produto inexistente
    # ANTES de qualquer erro de validação de corpo.
    api.add_url_rule("/produtos/<int:id>", "atualizar_produto",
                     exigir_admin(produtos.atualizar), methods=["PUT"])
    api.add_url_rule("/produtos/<int:id>", "deletar_produto",
                     exigir_admin(produtos.deletar), methods=["DELETE"])

    # --- usuários: cadastro de terceiro é dado privilegiado ----------------
    api.add_url_rule("/usuarios", "listar_usuarios",
                     exigir_admin(usuarios.listar), methods=["GET"])
    api.add_url_rule("/usuarios/<int:id>", "buscar_usuario",
                     exigir_dono_ou_admin("id")(usuarios.buscar), methods=["GET"])
    # Pública: sem ela não existe a primeira conta. O service grava sempre com
    # tipo 'cliente', então o registro não é caminho de escalada de privilégio.
    api.add_url_rule("/usuarios", "criar_usuario",
                     validar_corpo(usuario_schema)(usuarios.criar), methods=["POST"])
    # Pública: é a rota que emite o token.
    api.add_url_rule("/login", "login",
                     validar_corpo(login_schema)(usuarios.login), methods=["POST"])

    # --- pedidos: o próprio usuário; visão global e status são de admin ----
    api.add_url_rule("/pedidos", "criar_pedido",
                     exigir_dono_no_corpo("usuario_id")(
                         validar_corpo(pedido_schema)(pedidos.criar)),
                     methods=["POST"])
    api.add_url_rule("/pedidos", "listar_todos_pedidos",
                     exigir_admin(pedidos.listar), methods=["GET"])
    api.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
                     exigir_dono_ou_admin("usuario_id")(pedidos.listar_por_usuario),
                     methods=["GET"])
    api.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
                     exigir_admin(
                         validar_corpo(status_pedido_schema)(pedidos.atualizar_status)),
                     methods=["PUT"])

    # --- relatórios: faturamento da operação, só admin ---------------------
    api.add_url_rule("/relatorios/vendas", "relatorio_vendas",
                     exigir_admin(relatorios.vendas), methods=["GET"])

    app.register_blueprint(api)
