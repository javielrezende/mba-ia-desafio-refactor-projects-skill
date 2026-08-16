# Fase 1 — Heurísticas de análise de projeto

Objetivo: descrever o projeto com precisão, a partir de evidência no repositório. Nada aqui é julgamento de qualidade.

---

## 1. Delimitar o que é código-fonte

Antes de contar qualquer coisa, defina o conjunto de arquivos analisados.

**Excluir sempre:**

```
node_modules/  vendor/  .venv/  venv/  __pycache__/  dist/  build/  target/
.git/  .claude/  coverage/  *.min.js  *.lock  package-lock.json  *.db  *.sqlite
```

`.claude/` é o diretório da **própria skill**: seus arquivos de referência contêm exemplos de código (`SECRET_KEY = '...'`, `@app.route`, `print(...)`) que casam com os sinais de detecção. Contá-los infla a Fase 1 e gera falso-positivo na Fase 2.

Por isso todo `grep -r` deste arquivo e do `antipattern-catalog.md` carrega as exclusões inline:

```bash
--exclude-dir={.claude,node_modules,.venv,__pycache__}
```

Escreva o grupo `{...}` **literalmente** no comando. Não substitua por uma variável de shell (`$EXCL`): em `zsh` — shell padrão em muitos ambientes — uma variável não sofre word-splitting, o valor inteiro vira um único padrão de exclusão e nenhum diretório é filtrado, **sem erro nenhum**. A varredura parece limpa e continua casando com os arquivos da skill.

**Contagem (rode, não estime):**

```bash
# arquivos-fonte + linhas, Python
find . -name '*.py' -not -path './.claude/*' -not -path './.venv/*' -not -path './__pycache__/*' | xargs wc -l

# arquivos-fonte + linhas, JS/TS
find . \( -name '*.js' -o -name '*.ts' \) -not -path './.claude/*' -not -path './node_modules/*' | xargs wc -l
```

Arquivos de seed/migração e de teste contam como fonte, mas devem ser marcados como tal no resumo (ex.: `5 files analyzed (1 seed)`).

---

## 2. Detecção de linguagem e framework

Regra de precedência: **manifesto de dependências > imports no código > extensão de arquivo**. O manifesto dá a versão; os imports confirmam o uso real.

| Manifesto | Linguagem | Onde ler a versão do framework |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python | linha `flask==3.1.1`, `django==...`, `fastapi==...` |
| `package.json` | JavaScript / TypeScript | `dependencies.express`, `.fastify`, `.nestjs/core`, `.koa` |
| `composer.json` | PHP | `require.laravel/framework`, `.symfony/*`, `.slim/slim` |
| `go.mod` | Go | `github.com/gin-gonic/gin`, `.../echo` |
| `pom.xml`, `build.gradle` | Java | `spring-boot-starter-web` |
| `Gemfile` | Ruby | `rails`, `sinatra` |
| `Cargo.toml` | Rust | `actix-web`, `axum` |
| `*.csproj` | C# | `Microsoft.AspNetCore.*` |

**Confirmação por import (o framework precisa aparecer no código):**

- Flask → `from flask import Flask`, `app = Flask(__name__)`, decorators `@app.route` / `@bp.route`, `app.add_url_rule(...)`
- Django → `manage.py`, `settings.py`, `urls.py`, `INSTALLED_APPS`
- FastAPI → `from fastapi import FastAPI`, `@app.get`
- Express → `require('express')` / `import express`, `app.use(...)`, `app.listen(...)`, `router.get(...)`
- NestJS → decorators `@Controller`, `@Module`
- Laravel → `artisan`, `routes/web.php`, `Illuminate\`

Se o manifesto lista um pacote que o código nunca importa, registre como dependência declarada porém não usada — é insumo para um finding LOW de código morto na Fase 2.

Se **nenhum** framework web for detectado, diga "Framework: nenhum (script/CLI)" e adapte o MVC alvo na Fase 3 (a camada View vira a interface de entrada — CLI, worker, consumer).

---

## 3. Detecção de banco de dados e do modelo de dados

**Driver / ORM (pelo import):**

| Sinal | Banco / acesso |
|---|---|
| `import sqlite3`, `require('sqlite3')`, `better-sqlite3` | SQLite, SQL cru |
| `psycopg2`, `asyncpg`, `pg`, `postgres://` | PostgreSQL |
| `mysql.connector`, `PyMySQL`, `mysql2` | MySQL / MariaDB |
| `flask_sqlalchemy`, `sqlalchemy`, `db.Model` | SQLAlchemy (ORM) |
| `sequelize`, `typeorm`, `prisma`, `mongoose` | ORM/ODM JS |
| `django.db.models` | Django ORM |
| `pymongo`, `mongodb://` | MongoDB |
| nenhum dos acima, mas há `dict`/`array` global guardando registros | persistência em memória |

**Tabelas / entidades — três fontes, nesta ordem:**

1. `CREATE TABLE <nome>` no código ou em `.sql` — nome literal da tabela.
2. Classes de model do ORM (`class Task(db.Model)`, `__tablename__`, `sequelize.define('...')`).
3. Nomes que aparecem em `SELECT ... FROM <x>` / `INSERT INTO <x>` quando não houver DDL no repositório.

```bash
grep -rniE --exclude-dir={.claude,node_modules,.venv,__pycache__} "create table|__tablename__|db\.Model|INSERT INTO|FROM [a-z_]+" --include='*.py' --include='*.js' .
```

Registre também **onde** o schema vive: um `database.py` dedicado, um `.sql`, migrations — ou dentro de uma classe de aplicação (isso já antecipa um God Class na Fase 2).

---

## 4. Inferência do domínio

O domínio sai do cruzamento de três evidências, nunca do nome do diretório:

1. **Rotas** — `grep -rnE --exclude-dir={.claude,node_modules,.venv,__pycache__} "@[a-z_]*\.route|add_url_rule|(app|router)\.(get|post|put|delete)\(" .` (o prefixo do decorator é o nome do blueprint — `@task_bp.route`, não só `@app.route`)
2. **Tabelas/entidades** — do passo 3.
3. **README do projeto e arquivos de exemplo** (`api.http`, `*.rest`, coleções Postman) — costumam nomear o negócio e revelar o contrato esperado dos endpoints.

Escreva o domínio como uma frase concreta com as entidades reais: *"E-commerce API (produtos, pedidos, usuários)"*, *"LMS com fluxo de checkout (cursos, matrículas, pagamentos)"*, *"Task Manager (tasks, usuários, categorias, relatórios)"*. Não escreva "API REST genérica".

> Atenção a nomes enganosos: um diretório chamado `ecommerce-api` pode conter um LMS. Vale o que as tabelas e as rotas dizem.

---

## 5. Mapeamento da arquitetura atual

Classifique em um dos padrões abaixo e justifique em uma linha:

| Padrão | Sinais |
|---|---|
| **Monolítico sem camadas** | tudo em 1-4 arquivos na raiz; rotas, SQL e regra no mesmo arquivo |
| **God Class / God Module** | uma classe ou arquivo > ~150 linhas concentrando conexão de banco, schema, rotas e negócio |
| **Camadas nominais (vazando)** | existem `models.py`/`controllers.py`, mas o model tem regra de negócio e o controller tem SQL |
| **Camadas por pasta, sem controller/service** | existem `models/`, `routes/`, `services/`, mas a regra vive dentro do handler HTTP e `services/`/`utils/` estão mortos |
| **MVC real** | rota → controller → service → model, com dependências injetadas |

**Checagens que revelam vazamento de camada:**

```bash
# SQL dentro de arquivo de rota/controller
grep -rniE --exclude-dir={.claude,node_modules,.venv,__pycache__} "select |insert into|update .* set|delete from" --include='*routes*' --include='*controller*' .

# framework HTTP dentro de model/service (request/response fora da camada de entrada)
grep -rniE --exclude-dir={.claude,node_modules,.venv,__pycache__} "request\.|jsonify|res\.(send|json)|req\.body" --include='*model*' --include='*service*' .

# camadas mortas: arquivo existe mas ninguém importa
grep -rn --exclude-dir={.claude,node_modules,.venv,__pycache__} "notification_service\|helpers" --include='*.py' . | grep -i import
```

Um módulo dentro de `services/`/`utils/` que **nenhum arquivo importa** é camada morta — registre no mapa, vira finding LOW/MEDIUM na Fase 2.

Mapeie também o **entry point** (`if __name__ == "__main__"`, `main` do `package.json`, `scripts.start`) e como as dependências são construídas: instanciadas dentro dos próprios módulos (acoplamento) ou injetadas de fora.

---

## 6. Formato de saída da Fase 1

Imprima exatamente neste formato, com os valores reais:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

Regras do bloco:
- `Framework` inclui a versão do manifesto. Se não houver versão fixada, escreva `Express (^4.18.2, não fixado)`.
- `Dependencies` lista só as dependências diretas relevantes (não transitivas, não devDependencies triviais).
- `Architecture` é uma frase com o padrão detectado + a evidência.
- `Source files` bate com a contagem executada; acrescente `| ~N lines` quando útil.
- `DB tables` lista os nomes reais. Se o banco for em memória sem tabelas, escreva `nenhuma (estado em memória)`.
- Acrescente a linha `Entry point:` quando ele não for óbvio.
