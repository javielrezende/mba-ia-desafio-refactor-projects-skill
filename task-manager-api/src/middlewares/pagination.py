"""Paginação opcional das listagens.

Antes nenhuma listagem tinha LIMIT (finding 11 / AP-12). A paginação é opt-in:
sem `page`/`per_page` na query string, a resposta continua sendo a lista
completa, exatamente como o contrato atual. Quando o cliente pede, o limite é
aplicado e fica sujeito a MAX_PER_PAGE.
"""
from flask import jsonify

from src.config.constants import DEFAULT_PER_PAGE, MAX_PER_PAGE
from src.domain.errors import ValidationError


def get_pagination(args) -> tuple[int | None, int | None]:
    """Devolve (limit, offset), ou (None, None) quando o cliente não paginou."""
    if 'page' not in args and 'per_page' not in args:
        return None, None

    page = _positive_int(args.get('page', 1), 'page')
    per_page = _positive_int(args.get('per_page', DEFAULT_PER_PAGE), 'per_page')
    per_page = min(per_page, MAX_PER_PAGE)
    return per_page, (page - 1) * per_page


def _positive_int(raw, field: str) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValidationError(f'Parâmetro {field} deve ser um número inteiro')
    if value < 1:
        raise ValidationError(f'Parâmetro {field} deve ser maior que zero')
    return value


#: Header que expõe o total de registros da coleção, para o cliente saber
#: quantas páginas existem. Vai em header — e não no corpo — justamente para
#: que a resposta continue sendo o array puro do contrato original.
TOTAL_COUNT_HEADER = 'X-Total-Count'


def paginated_response(items, total, status=200):
    """Devolve a lista como array puro, com o total no header."""
    response = jsonify(items)
    response.headers[TOTAL_COUNT_HEADER] = str(total)
    return response, status
