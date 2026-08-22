"""Checagem de saúde: conectividade do banco e contagens. Sem dado de config."""


class HealthService:
    def __init__(self, database, produto_repository, usuario_repository, pedido_repository,
                 versao):
        self._db = database
        self._produtos = produto_repository
        self._usuarios = usuario_repository
        self._pedidos = pedido_repository
        self._versao = versao

    def status(self):
        with self._db.sessao() as conexao:
            contagens = {
                "produtos": self._produtos.contar(conexao),
                "usuarios": self._usuarios.contar(conexao),
                "pedidos": self._pedidos.contar(conexao),
            }
        return {
            "status": "ok",
            "database": "connected",
            "counts": contagens,
            "versao": self._versao,
        }
