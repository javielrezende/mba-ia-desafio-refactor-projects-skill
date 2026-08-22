"""Leitura tipada de variáveis de ambiente. Nenhum segredo literal vive aqui."""
import os

from dotenv import load_dotenv

load_dotenv()


def _obrigatoria(nome):
    valor = os.environ.get(nome)
    if not valor:
        raise RuntimeError(
            "Variável de ambiente obrigatória ausente: " + nome +
            ". Copie .env.example para .env e preencha os valores."
        )
    return valor


def _booleana(nome, padrao="false"):
    return os.getenv(nome, padrao).strip().lower() in ("1", "true", "yes")


class Settings:
    def __init__(self):
        # Sem default: o boot falha em vez de subir com um segredo previsível.
        self.SECRET_KEY = _obrigatoria("SECRET_KEY")
        self.DEBUG = _booleana("DEBUG", "false")
        self.DATABASE_PATH = os.getenv("DATABASE_PATH", "loja.db")
        self.HOST = os.getenv("HOST", "127.0.0.1")
        self.PORT = int(os.getenv("PORT", "5000"))
        self.CORS_ORIGINS = [
            origem.strip()
            for origem in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
            if origem.strip()
        ]
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        self.API_VERSION = os.getenv("API_VERSION", "1.0.0")


def carregar_settings():
    return Settings()
