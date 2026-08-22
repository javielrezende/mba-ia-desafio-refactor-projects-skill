"""Middleware de validação: schema aplicado antes do controller."""
from functools import wraps

from flask import request


def validar_corpo(schema):
    def decorador(handler):
        @wraps(handler)
        def wrapper(*args, **kwargs):
            corpo = request.get_json(silent=True)
            kwargs["dados"] = schema.validar(corpo)
            return handler(*args, **kwargs)
        return wrapper
    return decorador
