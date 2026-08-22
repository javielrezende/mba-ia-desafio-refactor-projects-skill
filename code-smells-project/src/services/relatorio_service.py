"""Relatório de vendas — as faixas de desconto vivem em config/constants."""
from src.config.constants import CASAS_DECIMAIS_MONETARIAS, FAIXAS_DESCONTO


def calcular_desconto(faturamento):
    for faturamento_minimo, percentual in FAIXAS_DESCONTO:
        if faturamento > faturamento_minimo:
            return faturamento * percentual
    return 0.0


class RelatorioService:
    def __init__(self, database, pedido_repository):
        self._db = database
        self._pedidos = pedido_repository

    def vendas(self):
        with self._db.sessao() as conexao:
            resumo = self._pedidos.resumo_vendas(conexao)

        faturamento = resumo["faturamento"]
        desconto = calcular_desconto(faturamento)
        total_pedidos = resumo["total_pedidos"]
        casas = CASAS_DECIMAIS_MONETARIAS

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, casas),
            "desconto_aplicavel": round(desconto, casas),
            "faturamento_liquido": round(faturamento - desconto, casas),
            "pedidos_pendentes": resumo["pendentes"],
            "pedidos_aprovados": resumo["aprovados"],
            "pedidos_cancelados": resumo["cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, casas) if total_pedidos > 0 else 0,
        }
