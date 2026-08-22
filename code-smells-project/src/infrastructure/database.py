"""Conexão e schema. Instanciado apenas pelo composition root e injetado."""
import sqlite3
from contextlib import contextmanager

from src.config.constants import TipoUsuario

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        preco REAL NOT NULL,
        estoque INTEGER NOT NULL,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha_hash TEXT NOT NULL,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
        status TEXT DEFAULT 'pendente',
        total REAL NOT NULL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
        -- SET NULL preserva o comportamento legado de deletar produto com histórico:
        -- o item permanece e a listagem mostra "Desconhecido", sem registro órfão.
        produto_id INTEGER REFERENCES produtos(id) ON DELETE SET NULL,
        quantidade INTEGER NOT NULL,
        preco_unitario REAL NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_itens_pedido_pedido_id ON itens_pedido(pedido_id)",
    "CREATE INDEX IF NOT EXISTS idx_itens_pedido_produto_id ON itens_pedido(produto_id)",
    "CREATE INDEX IF NOT EXISTS idx_pedidos_usuario_id ON pedidos(usuario_id)",
    "CREATE INDEX IF NOT EXISTS idx_pedidos_status ON pedidos(status)",
]

PRODUTOS_INICIAIS = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

# Senhas de desenvolvimento: entram no banco já como hash, nunca em texto puro.
USUARIOS_INICIAIS = [
    ("Admin", "admin@loja.com", "admin123", TipoUsuario.ADMIN.value),
    ("João Silva", "joao@email.com", "123456", TipoUsuario.CLIENTE.value),
    ("Maria Santos", "maria@email.com", "senha123", TipoUsuario.CLIENTE.value),
]


class Database:
    """Fábrica de conexões. Nenhuma conexão global, nenhum estado de módulo."""

    def __init__(self, caminho):
        self._caminho = caminho

    def _abrir(self):
        conexao = sqlite3.connect(self._caminho)
        conexao.row_factory = sqlite3.Row
        # Sem o PRAGMA, as FOREIGN KEY declaradas acima não são aplicadas.
        conexao.execute("PRAGMA foreign_keys = ON")
        return conexao

    @contextmanager
    def sessao(self):
        """Conexão de leitura, aberta e fechada por operação."""
        conexao = self._abrir()
        try:
            yield conexao
        finally:
            conexao.close()

    @contextmanager
    def transacao(self):
        """Escrita atômica: COMMIT no sucesso, ROLLBACK em qualquer exceção."""
        conexao = self._abrir()
        try:
            conexao.execute("BEGIN")
            yield conexao
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
        finally:
            conexao.close()

    def migrar(self, hash_de_senha):
        """Cria o schema e popula o seed apenas quando o banco está vazio."""
        with self.transacao() as conexao:
            for comando in SCHEMA:
                conexao.execute(comando)

            cursor = conexao.execute("SELECT COUNT(*) FROM produtos")
            if cursor.fetchone()[0] == 0:
                conexao.executemany(
                    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
                    "VALUES (?, ?, ?, ?, ?)",
                    PRODUTOS_INICIAIS,
                )
                conexao.executemany(
                    "INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES (?, ?, ?, ?)",
                    [
                        (nome, email, hash_de_senha(senha), tipo)
                        for nome, email, senha, tipo in USUARIOS_INICIAIS
                    ],
                )
