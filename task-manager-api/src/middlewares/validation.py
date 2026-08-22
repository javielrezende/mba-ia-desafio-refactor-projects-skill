"""Middleware de validação por schema.

Aplica o schema antes do controller, para que o controller receba dados já
validados e não repita bloco de if (findings 10 e 12).
"""
from functools import wraps

from flask import request
from marshmallow import ValidationError as MarshmallowValidationError

from src.domain.errors import ValidationError


def _first_message(errors: dict, field_order: list[str]) -> str:
    """Escolhe uma mensagem única, na ordem em que o código original checava.

    A API sempre devolveu {'error': '<mensagem>'}; manter esse formato evita
    mudar o contrato de erro só porque a validação passou a ser por schema.
    """
    for field in field_order:
        if field in errors:
            messages = errors[field]
            if isinstance(messages, dict):
                messages = next(iter(messages.values()), ['Dados inválidos'])
            return messages[0] if isinstance(messages, list) else str(messages)
    for messages in errors.values():
        if isinstance(messages, list) and messages:
            return messages[0]
    return 'Dados inválidos'


def validate_body(schema_class, field_order, reject_empty=True):
    """Valida o corpo JSON contra o schema e injeta o resultado em `data`.

    `reject_empty=False` aceita um corpo vazio (`{}`) como atualização sem
    efeito. Isso não é preferência de estilo: o `update_category` original
    (routes/report_routes.py:190-203) não tinha a guarda `if not data` que o
    `create_category` (:170-172) tinha, e devolvia 200 nesse caso. Uniformizar
    para 400 mudaria o contrato daquela rota.
    """

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            # get_json() sem argumentos preserva o 415 que o Flask já devolvia
            # quando o Content-Type não é application/json.
            payload = request.get_json(silent=True)
            if request.content_type is None or 'json' not in (request.content_type or ''):
                request.get_json()  # levanta UnsupportedMediaType (415)
            if not payload:
                if reject_empty:
                    raise ValidationError('Dados inválidos')
                payload = {}

            schema = schema_class()
            try:
                kwargs['data'] = schema.load(payload)
            except MarshmallowValidationError as err:
                raise ValidationError(_first_message(err.messages, field_order)) from err
            kwargs['raw_payload'] = payload
            kwargs['schema'] = schema
            return view(*args, **kwargs)

        return wrapper

    return decorator
