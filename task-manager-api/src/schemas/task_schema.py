"""Schemas de entrada da entidade Task.

Uma única definição das regras de formato, compartilhada por POST e PUT — antes
o mesmo bloco de validação estava copiado nos dois handlers e já havia divergido
(finding 10 / AP-13). Usa marshmallow, que estava em requirements.txt e nunca
era importado (finding 12 / AP-14).

As mensagens reproduzem literalmente as que a API já devolvia, para não mudar o
contrato de erro.
"""
from datetime import datetime

from marshmallow import EXCLUDE, Schema, ValidationError, fields, missing, validates_schema

from src.config.constants import (
    DATE_FORMAT,
    DEFAULT_PRIORITY,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    Status,
    VALID_STATUSES,
)

#: Ordem em que os erros são reportados, para espelhar a sequência de ifs do
#: código original (título antes de status, status antes de prioridade, ...).
TASK_ERROR_ORDER = ['title', 'status', 'priority', 'due_date', 'tags', 'user_id', 'category_id']


def _validate_title(value):
    if value is None or not str(value).strip():
        raise ValidationError('Título é obrigatório')
    if len(value) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(value) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')


def _validate_status(value):
    if value not in VALID_STATUSES:
        raise ValidationError('Status inválido')


def _validate_priority(value):
    if value < MIN_PRIORITY or value > MAX_PRIORITY:
        raise ValidationError('Prioridade deve ser entre 1 e 5')


class TagsField(fields.Field):
    """Aceita lista ou string, como o código original, e normaliza para string."""

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        if isinstance(value, list):
            return ','.join(str(tag) for tag in value)
        return str(value)


class TaskCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.Str(
        required=True,
        validate=_validate_title,
        error_messages={
            'required': 'Título é obrigatório',
            'invalid': 'Título é obrigatório',
            'null': 'Título é obrigatório',
        },
    )
    description = fields.Str(load_default='', allow_none=True)
    status = fields.Str(
        load_default=Status.PENDING.value,
        validate=_validate_status,
        error_messages={'invalid': 'Status inválido'},
    )
    priority = fields.Int(
        load_default=DEFAULT_PRIORITY,
        validate=_validate_priority,
        error_messages={'invalid': 'Prioridade deve ser entre 1 e 5', 'null': 'Prioridade deve ser entre 1 e 5'},
    )
    user_id = fields.Int(load_default=None, allow_none=True, error_messages={'invalid': 'Usuário inválido'})
    category_id = fields.Int(load_default=None, allow_none=True, error_messages={'invalid': 'Categoria inválida'})
    due_date = fields.Str(load_default=None, allow_none=True)
    tags = TagsField(load_default=None, allow_none=True)

    #: Mensagem usada quando a data não casa com o formato esperado.
    due_date_error = 'Formato de data inválido. Use YYYY-MM-DD'

    @validates_schema
    def _check_due_date(self, data, **kwargs):
        raw = data.get('due_date')
        if raw in (None, ''):
            return
        try:
            datetime.strptime(raw, DATE_FORMAT)
        except (ValueError, TypeError):
            raise ValidationError(self.due_date_error, field_name='due_date')

    def parse_due_date(self, raw):
        if raw in (None, ''):
            return None
        return datetime.strptime(raw, DATE_FORMAT)


class TaskUpdateSchema(TaskCreateSchema):
    """PUT parcial: reaproveita exatamente as mesmas regras do POST."""

    class Meta:
        unknown = EXCLUDE

    #: O PUT original devolvia a mensagem sem o sufixo do formato.
    due_date_error = 'Formato de data inválido'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('partial', True)
        super().__init__(*args, **kwargs)
        # Em atualização parcial nenhum campo é obrigatório e nada recebe default:
        # só o que o cliente mandou pode ser alterado.
        for field in self.fields.values():
            field.required = False
            # `missing` mantém o campo AUSENTE do resultado quando o cliente não
            # o enviou — é o que distingue "não mandou" de "mandou null".
            field.load_default = missing
