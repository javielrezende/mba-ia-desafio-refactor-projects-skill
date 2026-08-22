"""Error handler central.

Substitui os 12 `except:` nus espalhados pelos handlers, que devolviam
{'error': 'Erro interno'} sem registrar stack trace em lugar nenhum
(finding 6 / AP-10). Agora o erro sobe, é logado com traceback e a resposta
nunca expõe detalhe interno.
"""
from werkzeug.exceptions import HTTPException

from src.domain.errors import DomainError


def register_error_handlers(app, logger) -> None:
    @app.errorhandler(DomainError)
    def handle_domain_error(error: DomainError):
        logger.info('erro de domínio: %s (%s)', error.message, error.status_code)
        return {'error': error.message}, error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        # Preserva o status que o Flask já produzia (404 de rota inexistente,
        # 405, 415 de Content-Type ausente), mas responde em JSON — a API não
        # devolve mais página HTML de erro no meio de respostas JSON.
        logger.info('erro HTTP %s em %s', error.code, getattr(error, 'description', ''))
        return {'error': error.description}, error.code

    @app.errorhandler(Exception)
    def handle_unexpected(error: Exception):
        logger.exception('erro não tratado')
        return {'error': 'Erro interno'}, 500
