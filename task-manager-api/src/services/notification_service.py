"""Envio de notificações por e-mail.

O módulo original (services/notification_service.py) tinha 0 importadores: a
funcionalidade não existia, só a pasta sugeria que sim (finding 16 / AP-19).
Aqui ele é ligado ao fluxo — TaskService o aciona ao atribuir uma task — com as
credenciais vindas de variável de ambiente (finding 3) e log estruturado no
lugar dos print() (finding 15).

Com SMTP_ENABLED=false (default) nada é enviado: a intenção é apenas registrada.
Isso mantém o comportamento observável da API idêntico ao original, que também
nunca enviava e-mail nenhum.
"""
import smtplib
from email.message import EmailMessage


class NotificationService:
    def __init__(self, settings, logger):
        self._settings = settings
        self._logger = logger

    def send_email(self, to: str, subject: str, body: str) -> bool:
        if not self._settings.SMTP_ENABLED:
            self._logger.info('notificação suprimida (SMTP_ENABLED=false) destino=%s assunto=%s', to, subject)
            return False

        message = EmailMessage()
        message['From'] = self._settings.SMTP_USER
        message['To'] = to
        message['Subject'] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(self._settings.SMTP_HOST, self._settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                if self._settings.SMTP_USER:
                    server.login(self._settings.SMTP_USER, self._settings.SMTP_PASSWORD)
                server.send_message(message)
        except (smtplib.SMTPException, OSError):
            # Notificação é efeito colateral: falhar aqui não pode derrubar a
            # operação de negócio que a disparou.
            self._logger.exception('falha ao enviar notificação destino=%s', to)
            return False

        self._logger.info('notificação enviada destino=%s assunto=%s', to, subject)
        return True

    def notify_task_assigned(self, user, task) -> bool:
        return self.send_email(
            user.email,
            f'Nova task atribuída: {task.title}',
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f'Prioridade: {task.priority}\nStatus: {task.status}',
        )

    def notify_task_overdue(self, user, task) -> bool:
        return self.send_email(
            user.email,
            f'Task atrasada: {task.title}',
            f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}",
        )
