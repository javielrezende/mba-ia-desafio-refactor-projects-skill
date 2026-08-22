"""Notificação de pedido.

No código legado isto era um print("ENVIANDO EMAIL: ...") — funcionalidade
inexistente fingida por log. Aqui a intenção fica explícita e injetável: em
produção, troca-se esta implementação por um gateway real sem tocar no service
de pedido.
"""
from src.config.constants import StatusPedido


class NotificationService:
    def __init__(self, logger):
        self._logger = logger

    def pedido_criado(self, pedido_id, usuario_id):
        # Ainda não há gateway de e-mail/SMS configurado: registramos a intenção
        # em nível WARNING para não passar a impressão de que o envio ocorreu.
        self._logger.warning(
            "notificação de pedido criado não enviada (gateway não configurado)",
            extra={"pedido_id": pedido_id, "usuario_id": usuario_id},
        )

    def status_alterado(self, pedido_id, novo_status):
        if novo_status in (StatusPedido.APROVADO.value, StatusPedido.CANCELADO.value):
            self._logger.warning(
                "notificação de mudança de status não enviada (gateway não configurado)",
                extra={"pedido_id": pedido_id, "status": novo_status},
            )
