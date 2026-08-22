"""Regra de negócio de usuário e autenticação."""
import sqlite3

from src.config.constants import TipoUsuario
from src.domain.errors import CredenciaisInvalidasError, NaoEncontradoError, ValidacaoError
from src.models.usuario_model import serializar_sessao

USUARIO_NAO_ENCONTRADO = "Usuário não encontrado"
EMAIL_EM_USO = "Email já cadastrado"


class UsuarioService:
    def __init__(self, database, usuario_repository, hash_de_senha, verificar_senha,
                 hash_dummy):
        self._db = database
        self._usuarios = usuario_repository
        self._hash_de_senha = hash_de_senha
        self._verificar_senha = verificar_senha
        # Hash descartável usado quando o e-mail não existe, para o tempo de
        # resposta não denunciar quais contas estão cadastradas.
        self._hash_dummy = hash_dummy

    def listar(self, limite, deslocamento):
        with self._db.sessao() as conexao:
            return (
                self._usuarios.listar(conexao, limite, deslocamento),
                self._usuarios.contar(conexao),
            )

    def buscar(self, usuario_id):
        with self._db.sessao() as conexao:
            usuario = self._usuarios.buscar_por_id(conexao, usuario_id)
        if usuario is None:
            raise NaoEncontradoError(USUARIO_NAO_ENCONTRADO)
        return usuario

    def criar(self, dados):
        try:
            with self._db.transacao() as conexao:
                return self._usuarios.criar(
                    conexao,
                    dados["nome"],
                    dados["email"],
                    self._hash_de_senha(dados["senha"]),
                    TipoUsuario.CLIENTE.value,
                )
        except sqlite3.IntegrityError:
            raise ValidacaoError(EMAIL_EM_USO)

    def autenticar(self, email, senha):
        with self._db.sessao() as conexao:
            linha = self._usuarios.buscar_credenciais_por_email(conexao, email)

        # Verifica sempre — contra o hash real ou contra o dummy — para que os
        # dois caminhos custem o mesmo.
        hash_armazenado = linha["senha_hash"] if linha else self._hash_dummy
        senha_confere = self._verificar_senha(hash_armazenado, senha)

        if linha is None or not senha_confere:
            raise CredenciaisInvalidasError()
        return serializar_sessao(linha)
