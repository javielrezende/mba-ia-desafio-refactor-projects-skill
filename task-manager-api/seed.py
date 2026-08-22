"""Script para popular o banco com dados iniciais."""
from datetime import timedelta

from sqlalchemy import delete, func, select

from src.app import create_app
from src.config.constants import Status
from src.infrastructure.clock import utc_now
from src.infrastructure.database import db
from src.models.category_model import Category
from src.models.task_model import Task
from src.models.user_model import User

USERS = [
    {'name': 'João Silva', 'email': 'joao@email.com', 'password': 'senha1234', 'role': 'admin'},
    {'name': 'Maria Santos', 'email': 'maria@email.com', 'password': 'senha1234', 'role': 'user'},
    {'name': 'Pedro Oliveira', 'email': 'pedro@email.com', 'password': 'senha1234', 'role': 'manager'},
]

CATEGORIES = [
    {'name': 'Backend', 'description': 'Tarefas de backend', 'color': '#3498db'},
    {'name': 'Frontend', 'description': 'Tarefas de frontend', 'color': '#2ecc71'},
    {'name': 'DevOps', 'description': 'Tarefas de infraestrutura', 'color': '#e74c3c'},
    {'name': 'Bug', 'description': 'Correção de bugs', 'color': '#e67e22'},
]


def _tasks(users, categories, now):
    return [
        {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT',
         'status': Status.PENDING.value, 'priority': 1, 'user_id': users[0].id, 'category_id': categories[0].id,
         'due_date': now - timedelta(days=3)},
        {'title': 'Criar tela de login', 'description': 'Tela de login responsiva',
         'status': Status.IN_PROGRESS.value, 'priority': 2, 'user_id': users[1].id, 'category_id': categories[1].id,
         'due_date': now + timedelta(days=5)},
        {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions',
         'status': Status.DONE.value, 'priority': 2, 'user_id': users[2].id, 'category_id': categories[2].id,
         'tags': 'devops,ci,github'},
        {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais',
         'status': Status.PENDING.value, 'priority': 1, 'user_id': users[0].id, 'category_id': categories[3].id,
         'due_date': now - timedelta(days=1)},
        {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros',
         'status': Status.PENDING.value, 'priority': 3, 'user_id': users[0].id, 'category_id': categories[0].id,
         'due_date': now + timedelta(days=10)},
        {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%',
         'status': Status.PENDING.value, 'priority': 2, 'user_id': users[1].id, 'category_id': categories[0].id},
        {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática',
         'status': Status.CANCELLED.value, 'priority': 4, 'user_id': users[2].id, 'category_id': categories[0].id},
        {'title': 'Refatorar models', 'description': 'Melhorar organização dos models',
         'status': Status.IN_PROGRESS.value, 'priority': 3, 'user_id': users[1].id, 'category_id': categories[0].id,
         'tags': 'refactor,tech-debt'},
        {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana',
         'status': Status.PENDING.value, 'priority': 4, 'user_id': users[2].id, 'category_id': categories[2].id,
         'due_date': now + timedelta(days=20)},
        {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic',
         'status': Status.PENDING.value, 'priority': 3, 'user_id': users[0].id, 'category_id': categories[0].id,
         'tags': 'improvement,validation'},
    ]


def seed_data() -> None:
    app = create_app()
    with app.app_context():
        # Ordem respeita as chaves estrangeiras, agora que o PRAGMA as aplica.
        # delete() do SQLAlchemy 2.0 no lugar de Model.query.delete(), legado.
        db.session.execute(delete(Task))
        db.session.execute(delete(User))
        db.session.execute(delete(Category))
        db.session.commit()

        users = []
        for data in USERS:
            user = User()
            user.name = data['name']
            user.email = data['email']
            user.set_password(data['password'])
            user.role = data['role']
            db.session.add(user)
            users.append(user)

        categories = []
        for data in CATEGORIES:
            category = Category()
            category.name = data['name']
            category.description = data['description']
            category.color = data['color']
            db.session.add(category)
            categories.append(category)

        db.session.commit()

        for data in _tasks(users, categories, utc_now()):
            task = Task()
            for field, value in data.items():
                setattr(task, field, value)
            db.session.add(task)

        db.session.commit()

        def total(model):
            return db.session.scalar(select(func.count()).select_from(model))

        print('Seed concluído com sucesso!')
        print(f'  {total(User)} usuários')
        print(f'  {total(Category)} categorias')
        print(f'  {total(Task)} tasks')


if __name__ == '__main__':
    seed_data()
