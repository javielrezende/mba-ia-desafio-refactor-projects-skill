"""Regra de negócio de pedido: total, estoque e notificação, tudo em transação."""
from src.config.constants import StatusPedido
from src.domain.errors import NaoEncontradoError, RegraDeNegocioError

PEDIDO_NAO_ENCONTRADO = "Pedido não encontrado"
USUARIO_NAO_ENCONTRADO = "Usuário não encontrado"


class PedidoService:
    def __init__(self, database, pedido_repository, produto_repository,
                 usuario_repository, notificador):
        self._db = database
        self._pedidos = pedido_repository
        self._produtos = produto_repository
        self._usuarios = usuario_repository
        self._notificador = notificador

    def listar(self, limite, deslocamento):
        with self._db.sessao() as conexao:
            return (
                self._pedidos.listar(conexao, limite, deslocamento),
                self._pedidos.contar(conexao),
            )

    def listar_por_usuario(self, usuario_id, limite, deslocamento):
        with self._db.sessao() as conexao:
            return (
                self._pedidos.listar_por_usuario(conexao, usuario_id, limite, deslocamento),
                self._pedidos.contar_por_usuario(conexao, usuario_id),
            )

    def criar(self, usuario_id, itens):
        """Pedido, itens e baixa de estoque numa única transação."""
        with self._db.transacao() as conexao:
            if not self._usuarios.existe(conexao, usuario_id):
                raise RegraDeNegocioError(
                    "Usuário " + str(usuario_id) + " não encontrado", incluir_sucesso=True
                )

            total = 0.0
            precos = {}
            for item in itens:
                produto = self._produtos.buscar_por_id(conexao, item["produto_id"])
                if produto is None:
                    raise RegraDeNegocioError(
                        "Produto " + str(item["produto_id"]) + " não encontrado",
                        incluir_sucesso=True,
                    )
                if produto["estoque"] < item["quantidade"]:
                    raise RegraDeNegocioError(
                        "Estoque insuficiente para " + produto["nome"],
                        incluir_sucesso=True,
                    )
                precos[item["produto_id"]] = produto["preco"]
                total += produto["preco"] * item["quantidade"]

            pedido_id = self._pedidos.criar(
                conexao, usuario_id, StatusPedido.PENDENTE.value, total
            )
            for item in itens:
                preco_unitario = precos[item["produto_id"]]
                self._pedidos.adicionar_item(
                    conexao, pedido_id, item["produto_id"], item["quantidade"], preco_unitario
                )
                # Baixa condicional: se o estoque mudou entre a checagem e aqui,
                # a transação inteira volta atrás em vez de gravar estoque negativo.
                if not self._produtos.baixar_estoque(
                    conexao, item["produto_id"], item["quantidade"]
                ):
                    raise RegraDeNegocioError(
                        "Estoque insuficiente para o produto " + str(item["produto_id"]),
                        incluir_sucesso=True,
                    )

        resultado = {"pedido_id": pedido_id, "total": total}
        # Notificação fora da transação: falha de aviso não desfaz o pedido.
        self._notificador.pedido_criado(pedido_id, usuario_id)
        return resultado

    def atualizar_status(self, pedido_id, novo_status):
        with self._db.transacao() as conexao:
            self._pedidos.atualizar_status(conexao, pedido_id, novo_status)
        self._notificador.status_alterado(pedido_id, novo_status)
