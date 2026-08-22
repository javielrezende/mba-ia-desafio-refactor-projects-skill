"""Controllers de produto: entrada validada -> service -> resposta HTTP."""
from flask import jsonify, request

from src.domain.errors import ValidacaoError
from src.middlewares.pagination import meta, obter_paginacao


class ProdutoController:
    def __init__(self, produto_service):
        self._service = produto_service

    def listar(self):
        pagina, por_pagina, deslocamento = obter_paginacao(request.args)
        produtos, total = self._service.listar(por_pagina, deslocamento)
        return jsonify({
            "dados": produtos,
            "sucesso": True,
            "meta": meta(pagina, por_pagina, total),
        }), 200

    def buscar(self, id):
        return jsonify({"dados": self._service.buscar(id), "sucesso": True}), 200

    def pesquisar(self):
        pagina, por_pagina, deslocamento = obter_paginacao(request.args)
        resultados, total = self._service.pesquisar(
            request.args.get("q", ""),
            request.args.get("categoria"),
            _preco(request.args.get("preco_min"), "preco_min"),
            _preco(request.args.get("preco_max"), "preco_max"),
            por_pagina,
            deslocamento,
        )
        return jsonify({
            "dados": resultados,
            "total": total,
            "sucesso": True,
            "meta": meta(pagina, por_pagina, total),
        }), 200

    def criar(self, dados):
        produto_id = self._service.criar(dados)
        return jsonify({
            "dados": {"id": produto_id},
            "sucesso": True,
            "mensagem": "Produto criado",
        }), 201

    def atualizar(self, id):
        self._service.atualizar(id, request.get_json(silent=True))
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, id):
        self._service.deletar(id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def _preco(valor, rotulo):
    if valor is None or valor == "":
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise ValidacaoError("Parâmetro %s inválido" % rotulo)
