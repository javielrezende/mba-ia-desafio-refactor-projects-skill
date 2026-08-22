"""Schemas de pedido."""
from src.config.constants import StatusPedido
from src.domain.errors import ValidacaoError
from src.schemas.validators import Campo, Schema, um_de


def _itens_validos(itens):
    if not itens:
        raise ValidacaoError("Pedido deve ter pelo menos 1 item")
    for item in itens:
        if not isinstance(item, dict):
            raise ValidacaoError("Item inválido no pedido")
        if not isinstance(item.get("produto_id"), int) or isinstance(item.get("produto_id"), bool):
            raise ValidacaoError("Item inválido no pedido")
        quantidade = item.get("quantidade")
        if not isinstance(quantidade, int) or isinstance(quantidade, bool) or quantidade < 1:
            raise ValidacaoError("Quantidade inválida no pedido")


def _usuario_informado(valor):
    if not valor:
        raise ValidacaoError("Usuario ID é obrigatório")


pedido_schema = Schema([
    Campo("usuario_id", padrao=None, regras=(_usuario_informado,)),
    Campo("itens", padrao=[], regras=(_itens_validos,)),
])

status_pedido_schema = Schema([
    Campo("status", padrao="",
          regras=(um_de(StatusPedido.valores(), "Status inválido"),)),
], mensagem_corpo_vazio="Status inválido")
