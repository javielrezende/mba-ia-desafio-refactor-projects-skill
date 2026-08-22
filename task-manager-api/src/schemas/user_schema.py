"""Schemas de entrada da entidade User.

Regras de formato definidas uma vez e reaproveitadas por POST e PUT — antes o
regex de e-mail estava duplicado em user_routes.py:61 e :106, mais uma terceira
cópia em helpers.validate_email (finding 10 / AP-13).
"""
import re

from marshmallow import EXCLUDE, Schema, ValidationError, fields, missing

from src.config.constants import MIN_PASSWORD_LENGTH, VALID_ROLES, Role

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')

USER_ERROR_ORDER = ['name', 'email', 'password', 'role', 'active']


def _validate_email(value):
    if not value or not EMAIL_PATTERN.match(value):
        raise ValidationError('Email inválido')


def _validate_password(value):
    if value is None or len(value) < MIN_PASSWORD_LENGTH:
        # BREAKING CHANGE: o mínimo subiu de 4 para 8 caracteres (finding 12).
        raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')


def _validate_role(value):
    if value not in VALID_ROLES:
        raise ValidationError('Role inválido')


def _validate_name(value):
    if value is None or not str(value).strip():
        raise ValidationError('Nome é obrigatório')


class UserCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(
        required=True,
        validate=_validate_name,
        error_messages={'required': 'Nome é obrigatório', 'invalid': 'Nome é obrigatório', 'null': 'Nome é obrigatório'},
    )
    email = fields.Str(
        required=True,
        validate=_validate_email,
        error_messages={'required': 'Email é obrigatório', 'invalid': 'Email inválido', 'null': 'Email é obrigatório'},
    )
    password = fields.Str(
        required=True,
        validate=_validate_password,
        error_messages={
            'required': 'Senha é obrigatória',
            'invalid': 'Senha é obrigatória',
            'null': 'Senha é obrigatória',
        },
    )
    role = fields.Str(load_default=Role.USER.value, validate=_validate_role, error_messages={'invalid': 'Role inválido'})


class UserUpdateSchema(UserCreateSchema):
    """PUT parcial com as MESMAS regras do POST."""

    class Meta:
        unknown = EXCLUDE

    active = fields.Bool(error_messages={'invalid': 'Campo active deve ser booleano'})

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('partial', True)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False
            field.load_default = missing


class LoginSchema(Schema):
    """O login não aplica política de senha — só exige presença dos dois campos."""

    class Meta:
        unknown = EXCLUDE

    email = fields.Str(
        required=True,
        error_messages={'required': 'Email e senha são obrigatórios', 'null': 'Email e senha são obrigatórios'},
    )
    password = fields.Str(
        required=True,
        error_messages={'required': 'Email e senha são obrigatórios', 'null': 'Email e senha são obrigatórios'},
    )


LOGIN_ERROR_ORDER = ['email', 'password']
