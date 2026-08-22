"""Controllers de usuário e autenticação."""
from flask import jsonify, request

from src.middlewares.pagination import meta, obter_paginacao


class UsuarioController:
    def __init__(self, usuario_service):
        self._service = usuario_service

    def listar(self):
        pagina, por_pagina, deslocamento = obter_paginacao(request.args)
        usuarios, total = self._service.listar(por_pagina, deslocamento)
        return jsonify({
            "dados": usuarios,
            "sucesso": True,
            "meta": meta(pagina, por_pagina, total),
        }), 200

    def buscar(self, id):
        return jsonify({"dados": self._service.buscar(id), "sucesso": True}), 200

    def criar(self, dados):
        usuario_id = self._service.criar(dados)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self, dados):
        usuario = self._service.autenticar(dados["email"], dados["senha"])
        return jsonify({
            "dados": usuario,
            "sucesso": True,
            "mensagem": "Login OK",
        }), 200
