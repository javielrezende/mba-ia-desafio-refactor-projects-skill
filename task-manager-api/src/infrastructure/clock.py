"""Fonte de tempo da aplicação.

Isolar o relógio num módulo permite substituí-lo em teste, em vez de espalhar
datetime.utcnow() por 19 pontos da regra de negócio (finding 7 / AP-07), e
concentra num só lugar a migração da API deprecada (finding 13 / AP-15).
"""
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Instante atual em UTC, *naive*.

    As colunas DateTime do schema não guardam timezone e as linhas já gravadas
    são naive, então comparar com um datetime aware levantaria TypeError. Esta
    função usa a API não deprecada (datetime.now(timezone.utc)) e devolve o
    valor sem tzinfo, mantendo a compatibilidade com o schema existente.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_now() -> datetime:
    """Instante atual no fuso local — usado apenas pelo endpoint /health."""
    return datetime.now()
