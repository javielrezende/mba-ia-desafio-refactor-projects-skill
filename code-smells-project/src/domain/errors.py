"""Exceções de domínio. Services levantam estas; ninguém devolve tupla HTTP."""


class DomainError(Exception):
    status_code = 400

    def __init__(self, mensagem, incluir_sucesso=False):
        super().__init__(mensagem)
        self.mensagem = mensagem
        # O contrato legado é irregular: alguns erros trazem "sucesso": false,
        # outros não. A flag preserva a forma exata de cada resposta.
        self.incluir_sucesso = incluir_sucesso

    def to_payload(self):
        corpo = {"erro": self.mensagem}
        if self.incluir_sucesso:
            corpo["sucesso"] = False
        return corpo


class ValidacaoError(DomainError):
    status_code = 400


class NaoEncontradoError(DomainError):
    status_code = 404


class CredenciaisInvalidasError(DomainError):
    status_code = 401

    def __init__(self, mensagem="Email ou senha inválidos"):
        super().__init__(mensagem, incluir_sucesso=True)


class RegraDeNegocioError(DomainError):
    status_code = 400


class AutenticacaoError(DomainError):
    """401 — a requisição chegou sem credencial válida."""
    status_code = 401

    def __init__(self, mensagem="Autenticação obrigatória"):
        super().__init__(mensagem, incluir_sucesso=True)


class PermissaoError(DomainError):
    """403 — a credencial é válida, mas não tem o privilégio exigido pela rota."""
    status_code = 403

    def __init__(self, mensagem="Acesso negado"):
        super().__init__(mensagem, incluir_sucesso=True)
