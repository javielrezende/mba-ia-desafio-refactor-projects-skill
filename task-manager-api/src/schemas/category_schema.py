"""Schemas de entrada da entidade Category."""
from marshmallow import EXCLUDE, Schema, ValidationError, fields, missing

from src.config.constants import DEFAULT_CATEGORY_COLOR

CATEGORY_ERROR_ORDER = ['name', 'description', 'color']


def _validate_name(value):
    if value is None or not str(value).strip():
        raise ValidationError('Nome é obrigatório')


class CategoryCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(
        required=True,
        validate=_validate_name,
        error_messages={'required': 'Nome é obrigatório', 'invalid': 'Nome é obrigatório', 'null': 'Nome é obrigatório'},
    )
    description = fields.Str(load_default='', allow_none=True)
    color = fields.Str(load_default=DEFAULT_CATEGORY_COLOR, allow_none=True)


class CategoryUpdateSchema(CategoryCreateSchema):
    class Meta:
        unknown = EXCLUDE

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('partial', True)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False
            field.load_default = missing
