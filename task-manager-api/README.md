# task-manager-api

API de Task Manager em Python/Flask, organizada em camadas MVC.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env      # ajuste os valores; sem .env os defaults seguros valem
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000` (host e porta vêm de `HOST`/`PORT`).
O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e
tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints
vão retornar listas vazias.

Usuários do seed: `joao@email.com`, `maria@email.com`, `pedro@email.com` —
todos com a senha `senha1234`.

## Estrutura

```
app.py                      entry point: create_app() + app.run()
seed.py                     popula o banco com dados de exemplo
.env.example                todas as variáveis de ambiente suportadas
src/
├── app.py                  composition root: monta e injeta as dependências
├── config/
│   ├── settings.py         configuração lida do ambiente
│   └── constants.py        constantes e enums de domínio
├── domain/errors.py        exceções de domínio (viram status HTTP)
├── infrastructure/
│   ├── database.py         instância do ORM + PRAGMA foreign_keys
│   ├── clock.py            fonte de tempo (injetável em teste)
│   ├── logger.py           logging estruturado
│   └── security.py         hash de senha e emissão/validação de JWT
├── models/                 entidades do ORM + serialização
├── repositories/           acesso a dados por entidade
├── services/               regra de negócio (sem HTTP)
├── controllers/            entrada validada → service → resposta
├── views/routes.py         mapeamento rota → controller
├── schemas/                validação de entrada (marshmallow)
└── middlewares/            error handler, validação, paginação, auth
```

Regra das camadas: cada uma só conhece a de baixo. Um service nunca importa
`flask.request`; um controller nunca faz query.

## Configuração

Tudo por variável de ambiente — ver `.env.example`. Os defaults são seguros
(`DEBUG=false`, host local, CORS restrito a `http://localhost:3000`).

`SECRET_KEY` é obrigatória quando `FLASK_ENV=production`; em desenvolvimento uma
chave efêmera é gerada por processo.

## Autenticação

`POST /login` devolve um JWT HS256 assinado, com expiração (`TOKEN_TTL_SECONDS`).

A verificação do token é **opcional** e vem desligada. Com `AUTH_REQUIRED=true`:

- as rotas de escrita exigem `Authorization: Bearer <token>`;
- `DELETE /users/<id>` exige papel de administrador;
- `PUT /users/<id>` só é permitido ao próprio usuário ou a um administrador;
- definir ou alterar o campo `role` exige um administrador — o registro por
  `POST /users` continua aberto para o papel padrão `user`.

## Paginação

As listagens aceitam `?page=N&per_page=M` (teto de 100 por página) e devolvem o
total de registros no header `X-Total-Count`. Sem esses parâmetros a resposta
continua sendo a lista completa, preservando o contrato existente.
