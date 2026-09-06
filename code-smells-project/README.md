# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.
Refatorada para MVC em camadas — a auditoria que originou a mudança está em
`reports/audit-project-1.md`, na raiz do repositório.

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

Todo valor de ambiente vem de variável, nunca do código (`src/config/settings.py`).
Não existe variável que desligue a autenticação: o ambiente escolhe *qual* chave
assina o token e por *quanto tempo* ele vale, nunca *se* a verificação acontece.

| Variável | Obrigatória | Default | Descrição |
|---|---|---|---|
| `SECRET_KEY` | sim | — | Chave de assinatura. Sem ela o boot falha. |
| `DEBUG` | não | `false` | Modo debug do Flask. |
| `DATABASE_PATH` | não | `loja.db` | Caminho do arquivo SQLite. |
| `HOST` / `PORT` | não | `127.0.0.1` / `5000` | Bind do servidor. |
| `CORS_ORIGINS` | não | `http://localhost:3000` | Origens permitidas, separadas por vírgula. |
| `TOKEN_TTL_SECONDS` | não | `3600` | Validade do token emitido pelo login. |
| `LOG_LEVEL` | não | `INFO` | Nível do logger. |
| `API_VERSION` | não | `1.0.0` | Versão informada em `/` e `/health`. |

## Estrutura

```
app.py                      entry point — importa create_app() de src/
src/
├── app.py                  composition root: constrói e injeta dependências
├── config/                 settings (env) e constantes de domínio
├── domain/                 exceções de negócio
├── infrastructure/         conexão/schema do banco, logger e assinatura de token
├── models/                 repositórios por entidade, queries parametrizadas
├── services/               regra de negócio, sem HTTP
├── controllers/            orquestração: entrada validada → service → resposta
├── views/routes.py         rota → controller, com o gate de acesso de cada uma
├── middlewares/            auth (gate de acesso), error handler central, validação, paginação
└── schemas/                schemas de validação compartilhados entre POST e PUT
```

## Autenticação

`POST /login` devolve, além do corpo antigo, um `token` JWT HS256 assinado com a
`SECRET_KEY`. Apresente-o em todas as demais chamadas:

```bash
TOKEN=$(curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' \
  -d '{"email":"admin@loja.com","senha":"admin123"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

curl -H "Authorization: Bearer $TOKEN" localhost:5000/relatorios/vendas
```

Sem token a resposta é `401`; com token de privilégio insuficiente, `403`.

## Endpoints

Todas as rotas exigem `Authorization: Bearer <token>`, exceto as quatro marcadas
como públicas. A lista vive em `ROTAS_PUBLICAS`, no topo de `src/views/routes.py`.

| Rota | Acesso |
|---|---|
| `GET /` · `GET /health` | público — liveness, sem dado de negócio |
| `POST /login` | público — emite o token |
| `POST /usuarios` | público — registro; a conta é sempre criada como `cliente` |
| `GET /produtos` · `GET /produtos/busca` · `GET /produtos/<id>` | autenticado |
| `POST /produtos` · `PUT /produtos/<id>` · `DELETE /produtos/<id>` | admin |
| `GET /usuarios` | admin |
| `GET /usuarios/<id>` | dono ou admin |
| `POST /pedidos` | autenticado, e só para o próprio `usuario_id` (admin lança por qualquer um) |
| `GET /pedidos` · `PUT /pedidos/<id>/status` | admin |
| `GET /pedidos/usuario/<id>` | dono ou admin |
| `GET /relatorios/vendas` | admin |

As listagens aceitam `?page=` e `?per_page=` (teto de 100 itens) e devolvem um
bloco `meta` com `page`, `per_page` e `total`.

### Removidos por segurança

`POST /admin/query` (executava SQL arbitrário sem autenticação) e
`POST /admin/reset-db` (apagava as quatro tabelas sem autenticação) não existem
mais. `GET /usuarios` não devolve mais o campo `senha`; `GET /health` não devolve
mais `secret_key`, `debug`, `db_path` nem `ambiente`.

Além disso, **as 13 rotas de negócio passaram a exigir credencial**. Antes deste
gate, `GET /relatorios/vendas` entregava o faturamento da operação para qualquer
requisição anônima — remover os dois endpoints `/admin/*` fechava dois vetores e
deixava os outros treze abertos. Clientes que chamavam a API sem autenticar
precisam passar a fazer login.
