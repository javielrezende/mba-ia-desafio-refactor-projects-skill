"""Error handler central. Substitui os 19 try/except copiados nos handlers."""
from werkzeug.exceptions import HTTPException

from src.domain.errors import DomainError

ERRO_INTERNO = "Erro interno"


def registrar_error_handlers(app, logger):
    @app.errorhandler(DomainError)
    def _erro_de_dominio(erro):
        logger.warning("erro de domínio: %s", erro.mensagem)
        return erro.to_payload(), erro.status_code

    @app.errorhandler(HTTPException)
    def _erro_http(erro):
        return {"erro": erro.description}, erro.code

    @app.errorhandler(Exception)
    def _erro_inesperado(erro):
        # Stack trace vai para o log; a resposta nunca expõe detalhe interno.
        logger.exception("erro não tratado")
        return {"erro": ERRO_INTERNO}, 500
