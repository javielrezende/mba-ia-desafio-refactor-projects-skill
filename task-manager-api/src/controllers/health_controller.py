"""Controllers de disponibilidade e identificação da API."""
from flask import jsonify

from src.infrastructure.clock import local_now

API_NAME = 'Task Manager API'
API_VERSION = '1.0'


class HealthController:
    def health(self):
        # Devolve apenas estado e horário: nenhuma configuração da aplicação
        # vaza por aqui.
        return jsonify({'status': 'ok', 'timestamp': str(local_now())}), 200

    def index(self):
        return jsonify({'message': API_NAME, 'version': API_VERSION}), 200
