"""Motor de validação declarativo mínimo — sem dependência de framework HTTP.

As mensagens de erro reproduzem literalmente as do contrato legado.
"""
from src.domain.errors import ValidacaoError

FALTANDO = object()


class Campo:
    def __init__(self, nome, obrigatorio=False, mensagem_obrigatorio=None,
                 tipo=None, padrao=None, regras=()):
        self.nome = nome
        self.obrigatorio = obrigatorio
        self.mensagem_obrigatorio = mensagem_obrigatorio or ("%s é obrigatório" % nome)
        self.tipo = tipo
        self.padrao = padrao
        self.regras = regras


class Schema:
    def __init__(self, campos, mensagem_corpo_vazio="Dados inválidos"):
        self.campos = campos
        self.mensagem_corpo_vazio = mensagem_corpo_vazio

    def validar(self, corpo):
        if not corpo:
            raise ValidacaoError(self.mensagem_corpo_vazio)

        # Presença primeiro, na ordem declarada — a mesma do contrato legado.
        for campo in self.campos:
            if campo.obrigatorio and corpo.get(campo.nome, FALTANDO) is FALTANDO:
                raise ValidacaoError(campo.mensagem_obrigatorio)

        validado = {}
        for campo in self.campos:
            valor = corpo.get(campo.nome, FALTANDO)
            if valor is FALTANDO:
                validado[campo.nome] = campo.padrao
                continue
            if campo.tipo is not None:
                valor = campo.tipo(valor)
            validado[campo.nome] = valor

        # Regras de valor depois, também na ordem declarada.
        for campo in self.campos:
            for regra in campo.regras:
                regra(validado[campo.nome])

        return validado


def numero(rotulo):
    def converter(valor):
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ValidacaoError("%s deve ser um número" % rotulo)
        return valor
    return converter


def texto(rotulo):
    def converter(valor):
        if not isinstance(valor, str):
            raise ValidacaoError("%s deve ser um texto" % rotulo)
        return valor
    return converter


def minimo(limite, mensagem):
    def regra(valor):
        if valor is not None and valor < limite:
            raise ValidacaoError(mensagem)
    return regra


def comprimento_minimo(limite, mensagem):
    def regra(valor):
        if valor is not None and len(valor) < limite:
            raise ValidacaoError(mensagem)
    return regra


def comprimento_maximo(limite, mensagem):
    def regra(valor):
        if valor is not None and len(valor) > limite:
            raise ValidacaoError(mensagem)
    return regra


def um_de(valores, mensagem):
    def regra(valor):
        if valor not in valores:
            raise ValidacaoError(mensagem)
    return regra


def nao_vazio(mensagem):
    def regra(valor):
        if not valor:
            raise ValidacaoError(mensagem)
    return regra
