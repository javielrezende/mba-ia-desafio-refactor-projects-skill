"""Acesso a dados de produto. Queries parametrizadas, serialização única."""


def serializar(linha):
    """Único serializador de produto do projeto."""
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "descricao": linha["descricao"],
        "preco": linha["preco"],
        "estoque": linha["estoque"],
        "categoria": linha["categoria"],
        "ativo": linha["ativo"],
        "criado_em": linha["criado_em"],
    }


class ProdutoRepository:
    def listar(self, conexao, limite, deslocamento):
        cursor = conexao.execute(
            "SELECT * FROM produtos ORDER BY id LIMIT ? OFFSET ?",
            (limite, deslocamento),
        )
        return [serializar(linha) for linha in cursor.fetchall()]

    def contar(self, conexao):
        return conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]

    def buscar_por_id(self, conexao, produto_id):
        linha = conexao.execute(
            "SELECT * FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return serializar(linha) if linha else None

    def _filtros_pesquisa(self, termo, categoria, preco_min, preco_max):
        """Cláusula WHERE compartilhada pela busca e pela contagem da busca."""
        sql = ""
        parametros = []
        if termo:
            sql += " AND (nome LIKE ? OR descricao LIKE ?)"
            # Os curingas fazem parte do VALOR, nunca da string da query.
            parametros.extend(["%" + termo + "%", "%" + termo + "%"])
        if categoria:
            sql += " AND categoria = ?"
            parametros.append(categoria)
        if preco_min is not None:
            sql += " AND preco >= ?"
            parametros.append(preco_min)
        if preco_max is not None:
            sql += " AND preco <= ?"
            parametros.append(preco_max)
        return sql, parametros

    def pesquisar(self, conexao, termo, categoria, preco_min, preco_max, limite, deslocamento):
        filtros, parametros = self._filtros_pesquisa(termo, categoria, preco_min, preco_max)
        cursor = conexao.execute(
            "SELECT * FROM produtos WHERE 1=1" + filtros + " ORDER BY id LIMIT ? OFFSET ?",
            tuple(parametros + [limite, deslocamento]),
        )
        return [serializar(linha) for linha in cursor.fetchall()]

    def contar_pesquisa(self, conexao, termo, categoria, preco_min, preco_max):
        """Total de resultados da busca, independente da página."""
        filtros, parametros = self._filtros_pesquisa(termo, categoria, preco_min, preco_max)
        return conexao.execute(
            "SELECT COUNT(*) FROM produtos WHERE 1=1" + filtros, tuple(parametros)
        ).fetchone()[0]

    def criar(self, conexao, nome, descricao, preco, estoque, categoria):
        cursor = conexao.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
            "VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        return cursor.lastrowid

    def atualizar(self, conexao, produto_id, nome, descricao, preco, estoque, categoria):
        conexao.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, "
            "categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )

    def deletar(self, conexao, produto_id):
        conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def baixar_estoque(self, conexao, produto_id, quantidade):
        """Baixa condicional: a própria query garante que o estoque não fica negativo."""
        cursor = conexao.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
            (quantidade, produto_id, quantidade),
        )
        return cursor.rowcount == 1
