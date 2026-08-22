"""Constantes de domínio. Nenhum literal de negócio solto em handler."""
from enum import Enum


class StatusPedido(str, Enum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    ENVIADO = "enviado"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"

    @classmethod
    def valores(cls):
        return [status.value for status in cls]


class TipoUsuario(str, Enum):
    CLIENTE = "cliente"
    ADMIN = "admin"


CATEGORIAS_VALIDAS = [
    "informatica",
    "moveis",
    "vestuario",
    "geral",
    "eletronicos",
    "livros",
]
CATEGORIA_PADRAO = "geral"

MIN_NOME_PRODUTO = 2
MAX_NOME_PRODUTO = 200
MIN_SENHA = 8

# (faturamento mínimo, percentual de desconto) — avaliadas da maior para a menor.
FAIXAS_DESCONTO = (
    (10_000, 0.10),
    (5_000, 0.05),
    (1_000, 0.02),
)

CASAS_DECIMAIS_MONETARIAS = 2

PAGINA_PADRAO = 1
ITENS_POR_PAGINA_PADRAO = 100
MAX_ITENS_POR_PAGINA = 100

PRODUTO_DESCONHECIDO = "Desconhecido"
