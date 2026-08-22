"""Acesso a dados de usuário. A serialização pública nunca inclui credencial."""


def serializar(linha):
    """Único serializador de usuário — sem senha, sem hash."""
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "email": linha["email"],
        "tipo": linha["tipo"],
        "criado_em": linha["criado_em"],
    }


def serializar_sessao(linha):
    """Forma reduzida devolvida pelo login."""
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "email": linha["email"],
        "tipo": linha["tipo"],
    }


class UsuarioRepository:
    def listar(self, conexao, limite, deslocamento):
        cursor = conexao.execute(
            "SELECT * FROM usuarios ORDER BY id LIMIT ? OFFSET ?",
            (limite, deslocamento),
        )
        return [serializar(linha) for linha in cursor.fetchall()]

    def contar(self, conexao):
        return conexao.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]

    def buscar_por_id(self, conexao, usuario_id):
        linha = conexao.execute(
            "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return serializar(linha) if linha else None

    def existe(self, conexao, usuario_id):
        return conexao.execute(
            "SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone() is not None

    def buscar_credenciais_por_email(self, conexao, email):
        """Uso interno da autenticação: devolve a linha crua, com o hash."""
        return conexao.execute(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        ).fetchone()

    def criar(self, conexao, nome, email, senha_hash, tipo):
        cursor = conexao.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, tipo),
        )
        return cursor.lastrowid
