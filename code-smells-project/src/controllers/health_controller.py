"""Controllers de health check e index."""
from flask import jsonify


class HealthController:
    def __init__(self, health_service, versao):
        self._service = health_service
        self._versao = versao

    def health(self):
        return jsonify(self._service.status()), 200

    def index(self):
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": self._versao,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }), 200
