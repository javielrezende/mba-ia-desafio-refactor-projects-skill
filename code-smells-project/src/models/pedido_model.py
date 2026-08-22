"""Acesso a dados de pedido. A listagem usa JOIN — sem query dentro de laço."""
from src.config.constants import PRODUTO_DESCONHECIDO, StatusPedido

SQL_PEDIDOS_COM_ITENS = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario,
           pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr    ON pr.id = i.produto_id
    WHERE p.id IN ({placeholders})
    ORDER BY p.id, i.id
"""


def _cabecalho(linha):
    return {
        "id": linha["id"],
        "usuario_id": linha["usuario_id"],
        "status": linha["status"],
        "total": linha["total"],
        "criado_em": linha["criado_em"],
        "itens": [],
    }


class PedidoRepository:
    def _montar(self, conexao, ids_pedidos):
        """1 query para os itens de N pedidos, agrupados em memória."""
        if not ids_pedidos:
            return []

        placeholders = ",".join("?" for _ in ids_pedidos)
        cursor = conexao.execute(
            SQL_PEDIDOS_COM_ITENS.format(placeholders=placeholders),
            tuple(ids_pedidos),
        )

        pedidos = {}
        for linha in cursor.fetchall():
            pedido = pedidos.setdefault(linha["id"], _cabecalho(linha))
            if linha["quantidade"] is None:
                continue
            pedido["itens"].append({
                "produto_id": linha["produto_id"],
                "produto_nome": linha["produto_nome"] or PRODUTO_DESCONHECIDO,
                "quantidade": linha["quantidade"],
                "preco_unitario": linha["preco_unitario"],
            })
        # Preserva a ordem pedida, não a ordem do dicionário.
        return [pedidos[pedido_id] for pedido_id in ids_pedidos if pedido_id in pedidos]

    def listar(self, conexao, limite, deslocamento):
        ids = [
            linha["id"]
            for linha in conexao.execute(
                "SELECT id FROM pedidos ORDER BY id LIMIT ? OFFSET ?",
                (limite, deslocamento),
            ).fetchall()
        ]
        return self._montar(conexao, ids)

    def listar_por_usuario(self, conexao, usuario_id, limite, deslocamento):
        ids = [
            linha["id"]
            for linha in conexao.execute(
                "SELECT id FROM pedidos WHERE usuario_id = ? ORDER BY id LIMIT ? OFFSET ?",
                (usuario_id, limite, deslocamento),
            ).fetchall()
        ]
        return self._montar(conexao, ids)

    def contar(self, conexao):
        return conexao.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]

    def contar_por_usuario(self, conexao, usuario_id):
        return conexao.execute(
            "SELECT COUNT(*) FROM pedidos WHERE usuario_id = ?", (usuario_id,)
        ).fetchone()[0]

    def criar(self, conexao, usuario_id, status, total):
        cursor = conexao.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, status, total),
        )
        return cursor.lastrowid

    def adicionar_item(self, conexao, pedido_id, produto_id, quantidade, preco_unitario):
        conexao.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
            "VALUES (?, ?, ?, ?)",
            (pedido_id, produto_id, quantidade, preco_unitario),
        )

    def atualizar_status(self, conexao, pedido_id, novo_status):
        conexao.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)
        )

    def resumo_vendas(self, conexao):
        """Uma agregação no banco no lugar de cinco varreduras da tabela."""
        linha = conexao.execute(
            """
            SELECT COUNT(*) AS total_pedidos,
                   COALESCE(SUM(total), 0) AS faturamento,
                   COALESCE(SUM(status = ?), 0) AS pendentes,
                   COALESCE(SUM(status = ?), 0) AS aprovados,
                   COALESCE(SUM(status = ?), 0) AS cancelados
            FROM pedidos
            """,
            (StatusPedido.PENDENTE.value, StatusPedido.APROVADO.value,
             StatusPedido.CANCELADO.value),
        ).fetchone()
        return {
            "total_pedidos": linha["total_pedidos"],
            "faturamento": linha["faturamento"],
            "pendentes": linha["pendentes"],
            "aprovados": linha["aprovados"],
            "cancelados": linha["cancelados"],
        }
