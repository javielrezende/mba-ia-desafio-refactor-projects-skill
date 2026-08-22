"""Paginação com teto — nenhuma listagem devolve a tabela inteira."""
from src.config.constants import (
    ITENS_POR_PAGINA_PADRAO,
    MAX_ITENS_POR_PAGINA,
    PAGINA_PADRAO,
)
from src.domain.errors import ValidacaoError


def _inteiro(valor, padrao, rotulo):
    if valor is None or valor == "":
        return padrao
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValidacaoError("Parâmetro %s inválido" % rotulo)


def obter_paginacao(args):
    """Devolve (pagina, por_pagina, deslocamento) a partir da query string."""
    pagina = max(PAGINA_PADRAO, _inteiro(args.get("page"), PAGINA_PADRAO, "page"))
    por_pagina = _inteiro(args.get("per_page"), ITENS_POR_PAGINA_PADRAO, "per_page")
    por_pagina = min(MAX_ITENS_POR_PAGINA, max(1, por_pagina))
    return pagina, por_pagina, (pagina - 1) * por_pagina


def meta(pagina, por_pagina, total):
    return {"page": pagina, "per_page": por_pagina, "total": total}
