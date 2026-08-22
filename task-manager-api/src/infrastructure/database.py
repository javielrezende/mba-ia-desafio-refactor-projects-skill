"""Instância do ORM e configuração da conexão.

A instância é criada aqui mas só é ligada a uma aplicação pelo composition root
(src/app.py), via db.init_app(). Nenhum módulo de domínio abre a própria conexão.
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


@event.listens_for(Engine, 'connect')
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """Ativa a aplicação de chaves estrangeiras no SQLite.

    Sem este PRAGMA o SQLite aceita a FK declarada e não a aplica — era o que
    permitia DELETE /categories/<id> deixar tasks apontando para uma categoria
    inexistente (finding 8 / AP-09).
    """
    if type(dbapi_connection).__module__.startswith('sqlite3'):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')
        cursor.close()
