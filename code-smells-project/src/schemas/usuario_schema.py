"""Schemas de usuário e de login."""
from src.config.constants import MIN_SENHA
from src.schemas.validators import Campo, Schema, comprimento_minimo, nao_vazio, texto

MENSAGEM_CAMPOS_USUARIO = "Nome, email e senha são obrigatórios"
MENSAGEM_CAMPOS_LOGIN = "Email e senha são obrigatórios"

usuario_schema = Schema([
    Campo("nome", padrao="", tipo=texto("Nome"),
          regras=(nao_vazio(MENSAGEM_CAMPOS_USUARIO),)),
    Campo("email", padrao="", tipo=texto("Email"),
          regras=(nao_vazio(MENSAGEM_CAMPOS_USUARIO),)),
    Campo("senha", padrao="", tipo=texto("Senha"),
          regras=(nao_vazio(MENSAGEM_CAMPOS_USUARIO),
                  comprimento_minimo(
                      MIN_SENHA,
                      "Senha deve ter ao menos %d caracteres" % MIN_SENHA))),
])

login_schema = Schema([
    Campo("email", padrao="", tipo=texto("Email"),
          regras=(nao_vazio(MENSAGEM_CAMPOS_LOGIN),)),
    Campo("senha", padrao="", tipo=texto("Senha"),
          regras=(nao_vazio(MENSAGEM_CAMPOS_LOGIN),)),
], mensagem_corpo_vazio=MENSAGEM_CAMPOS_LOGIN)
