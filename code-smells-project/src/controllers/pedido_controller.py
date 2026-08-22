"""Controllers de pedido."""
from flask import jsonify, request

from src.middlewares.pagination import meta, obter_paginacao


class PedidoController:
    def __init__(self, pedido_service):
        self._service = pedido_service

    def criar(self, dados):
        resultado = self._service.criar(dados["usuario_id"], dados["itens"])
        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201

    def listar(self):
        pagina, por_pagina, deslocamento = obter_paginacao(request.args)
        pedidos, total = self._service.listar(por_pagina, deslocamento)
        return jsonify({
            "dados": pedidos,
            "sucesso": True,
            "meta": meta(pagina, por_pagina, total),
        }), 200

    def listar_por_usuario(self, usuario_id):
        pagina, por_pagina, deslocamento = obter_paginacao(request.args)
        pedidos, total = self._service.listar_por_usuario(usuario_id, por_pagina, deslocamento)
        return jsonify({
            "dados": pedidos,
            "sucesso": True,
            "meta": meta(pagina, por_pagina, total),
        }), 200

    def atualizar_status(self, pedido_id, dados):
        self._service.atualizar_status(pedido_id, dados["status"])
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
