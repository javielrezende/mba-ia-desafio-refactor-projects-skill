# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.
Refatorada para MVC em camadas — a auditoria que originou a mudança está em
`reports/audit-code-smells-project.md`, na raiz do repositório.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env      # preencha SECRET_KEY — a aplicação não sobe sem ela
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (host e porta configuráveis por
`HOST`/`PORT`). O banco SQLite é criado automaticamente no primeiro boot, já com
produtos e usuários de exemplo. As senhas do seed entram no banco como hash.

## Configuração

Todo valor de ambiente vem de variável, nunca do código (`src/config/settings.py`):

| Variável | Obrigatória | Default | Descrição |
|---|---|---|---|
| `SECRET_KEY` | sim | — | Chave de assinatura. Sem ela o boot falha. |
| `DEBUG` | não | `false` | Modo debug do Flask. |
| `DATABASE_PATH` | não | `loja.db` | Caminho do arquivo SQLite. |
| `HOST` / `PORT` | não | `127.0.0.1` / `5000` | Bind do servidor. |
| `CORS_ORIGINS` | não | `http://localhost:3000` | Origens permitidas, separadas por vírgula. |
| `LOG_LEVEL` | não | `INFO` | Nível do logger. |
| `API_VERSION` | não | `1.0.0` | Versão informada em `/` e `/health`. |

## Estrutura

```
app.py                      entry point — importa create_app() de src/
src/
├── app.py                  composition root: constrói e injeta dependências
├── config/                 settings (env) e constantes de domínio
├── domain/                 exceções de negócio
├── infrastructure/         conexão/schema do banco e logger
├── models/                 repositórios por entidade, queries parametrizadas
├── services/               regra de negócio, sem HTTP
├── controllers/            orquestração: entrada validada → service → resposta
├── views/routes.py         rota → controller
├── middlewares/            error handler central, validação, paginação
└── schemas/                schemas de validação compartilhados entre POST e PUT
```

## Endpoints

`GET /` · `GET /health` · `GET|POST /produtos` · `GET /produtos/busca` ·
`GET|PUT|DELETE /produtos/<id>` · `GET|POST /usuarios` · `GET /usuarios/<id>` ·
`POST /login` · `GET|POST /pedidos` · `GET /pedidos/usuario/<id>` ·
`PUT /pedidos/<id>/status` · `GET /relatorios/vendas`

As listagens aceitam `?page=` e `?per_page=` (teto de 100 itens) e devolvem um
bloco `meta` com `page`, `per_page` e `total`.

### Removidos por segurança

`POST /admin/query` (executava SQL arbitrário sem autenticação) e
`POST /admin/reset-db` (apagava as quatro tabelas sem autenticação) não existem
mais. `GET /usuarios` não devolve mais o campo `senha`; `GET /health` não devolve
mais `secret_key`, `debug`, `db_path` nem `ambiente`.
