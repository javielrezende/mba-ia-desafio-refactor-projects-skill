"""Regra de negócio de produto. Sem request, sem jsonify, sem SQL."""
from src.domain.errors import NaoEncontradoError
from src.schemas.produto_schema import produto_schema

PRODUTO_NAO_ENCONTRADO = "Produto não encontrado"


class ProdutoService:
    def __init__(self, database, produto_repository):
        self._db = database
        self._produtos = produto_repository

    def listar(self, limite, deslocamento):
        with self._db.sessao() as conexao:
            return (
                self._produtos.listar(conexao, limite, deslocamento),
                self._produtos.contar(conexao),
            )

    def pesquisar(self, termo, categoria, preco_min, preco_max, limite, deslocamento):
        with self._db.sessao() as conexao:
            return (
                self._produtos.pesquisar(
                    conexao, termo, categoria, preco_min, preco_max, limite, deslocamento
                ),
                # "total" no contrato legado é o total de resultados da busca,
                # não o tamanho da página.
                self._produtos.contar_pesquisa(
                    conexao, termo, categoria, preco_min, preco_max
                ),
            )

    def buscar(self, produto_id):
        with self._db.sessao() as conexao:
            produto = self._produtos.buscar_por_id(conexao, produto_id)
        if produto is None:
            raise NaoEncontradoError(PRODUTO_NAO_ENCONTRADO, incluir_sucesso=True)
        return produto

    def criar(self, dados):
        with self._db.transacao() as conexao:
            return self._produtos.criar(
                conexao,
                dados["nome"],
                dados["descricao"],
                dados["preco"],
                dados["estoque"],
                dados["categoria"],
            )

    def atualizar(self, produto_id, corpo):
        with self._db.transacao() as conexao:
            if self._produtos.buscar_por_id(conexao, produto_id) is None:
                raise NaoEncontradoError(PRODUTO_NAO_ENCONTRADO)
            # Mesmo schema do POST: a divergência de validação entre criar e
            # atualizar deixa de existir por construção.
            dados = produto_schema.validar(corpo)
            self._produtos.atualizar(
                conexao,
                produto_id,
                dados["nome"],
                dados["descricao"],
                dados["preco"],
                dados["estoque"],
                dados["categoria"],
            )

    def deletar(self, produto_id):
        with self._db.transacao() as conexao:
            if self._produtos.buscar_por_id(conexao, produto_id) is None:
                raise NaoEncontradoError(PRODUTO_NAO_ENCONTRADO)
            self._produtos.deletar(conexao, produto_id)
