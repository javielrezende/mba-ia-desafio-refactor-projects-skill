"""Logger estruturado da aplicação.

Substitui os 11 print() que serviam de log (finding 15 / AP-17) e a função
log_action() de utils/helpers.py:36, que fingia ser um logger e nunca era chamada.
"""
import logging

from src.config.settings import settings

_configured = False


def configure_logging() -> logging.Logger:
    """Configura o logging uma única vez, a partir do composition root."""
    global _configured
    if not _configured:
        logging.basicConfig(
            level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
            format='%(asctime)s %(levelname)-8s %(name)s %(message)s',
        )
        _configured = True
    return logging.getLogger('taskmanager')


def get_logger(name: str = 'taskmanager') -> logging.Logger:
    return logging.getLogger(name)
