"""Configuração da aplicação, lida de variáveis de ambiente.

Substitui os literais de app.py:11-15 (SECRET_KEY, URI do banco, debug, CORS) e
as credenciais de SMTP de services/notification_service.py:7-10 (finding 3 / AP-02).

python-dotenv já estava declarado em requirements.txt e nunca era importado.
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: str = 'false') -> bool:
    return os.getenv(name, default).strip().lower() in ('1', 'true', 'yes', 'on')


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == '':
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f'Variável de ambiente {name} deve ser um inteiro, recebido {raw!r}') from exc


class Settings:
    """Valores de configuração com defaults seguros.

    Segredo obrigatório falha no boot quando ausente fora de desenvolvimento:
    melhor não subir do que subir com uma chave previsível.
    """

    ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = _bool('DEBUG', 'false')

    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = _int('PORT', 5000)

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CORS_ORIGINS = [o.strip() for o in os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',') if o.strip()]

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

    #: Não existe flag de autenticação, de propósito. Configuração escolhe *qual*
    #: chave assina o token e por *quanto tempo* ele vale — nunca *se* a
    #: verificação acontece. A primeira passagem desta refatoração tinha um
    #: AUTH_REQUIRED com default `false`, e com ele DELETE /users/<id> respondia
    #: 200 sem token: o controle existia no código e estava ausente na prática.
    TOKEN_TTL_SECONDS = _int('TOKEN_TTL_SECONDS', 3600)

    SMTP_HOST = os.getenv('SMTP_HOST', 'localhost')
    SMTP_PORT = _int('SMTP_PORT', 587)
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_ENABLED = _bool('SMTP_ENABLED', 'false')

    def __init__(self) -> None:
        secret = os.getenv('SECRET_KEY')
        if not secret:
            if self.ENV == 'production':
                raise RuntimeError(
                    'SECRET_KEY é obrigatória em produção. Defina a variável de ambiente '
                    '(veja .env.example) — não há default.'
                )
            # Em desenvolvimento, gera uma chave efêmera por processo em vez de
            # cair num literal versionado. Reiniciar invalida os tokens emitidos.
            secret = os.urandom(32).hex()
        self.SECRET_KEY = secret


settings = Settings()
