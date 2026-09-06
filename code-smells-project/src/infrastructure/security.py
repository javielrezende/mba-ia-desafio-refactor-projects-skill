"""Emissão e verificação do token de sessão.

O código legado tinha um `/login` que conferia a senha e devolvia o dicionário do
usuário — e nada mais. Nenhuma rota exigia aquele resultado, então a API inteira
respondia a qualquer anônimo, inclusive `GET /relatorios/vendas` (finding 4 /
AP-04). Emitir credencial é a metade da correção; a outra metade é o gate em
middlewares/auth.py. Ver RP-04 e RP-17 no playbook da skill.

Nenhuma dependência nova: JWT HS256 montado com a stdlib (hmac + hashlib +
base64), que é exatamente a construção que a especificação HS256 define.
"""
import base64
import hashlib
import hmac
import json
import time


def _b64url(bruto):
    return base64.urlsafe_b64encode(bruto).rstrip(b"=").decode("ascii")


def _b64url_decode(dado):
    return base64.urlsafe_b64decode(dado + "=" * (-len(dado) % 4))


class TokenSigner:
    """Assina e valida o token. Recebe o segredo por injeção, como todo o resto."""

    def __init__(self, secret, ttl_segundos, agora=time.time):
        self._secret = secret.encode()
        self._ttl = ttl_segundos
        self._agora = agora

    def _assinar(self, entrada):
        return _b64url(hmac.new(self._secret, entrada, hashlib.sha256).digest())

    def emitir(self, usuario_id, tipo):
        cabecalho = {"alg": "HS256", "typ": "JWT"}
        corpo = {
            "sub": usuario_id,
            "tipo": tipo,
            "exp": int(self._agora()) + self._ttl,
        }
        partes = [
            _b64url(json.dumps(cabecalho, separators=(",", ":")).encode()),
            _b64url(json.dumps(corpo, separators=(",", ":")).encode()),
        ]
        partes.append(self._assinar(".".join(partes).encode("ascii")))
        return ".".join(partes)

    def decodificar(self, token):
        """Devolve o payload quando assinatura e expiração conferem; senão None."""
        try:
            cabecalho, corpo, assinatura = token.split(".")
        except (ValueError, AttributeError):
            return None

        esperada = self._assinar(("%s.%s" % (cabecalho, corpo)).encode("ascii"))
        # compare_digest: comparação em tempo constante, sem vazar o prefixo certo.
        if not hmac.compare_digest(esperada, assinatura):
            return None

        try:
            payload = json.loads(_b64url_decode(corpo))
        except (ValueError, TypeError):
            return None

        if int(payload.get("exp", 0)) < int(self._agora()):
            return None
        return payload
