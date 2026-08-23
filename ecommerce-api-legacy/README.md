# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express, refatorada para MVC em camadas
pela skill `refactor-arch`.

## Como rodar

```bash
npm install
cp .env.example .env   # opcional em desenvolvimento
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória por
padrão (`DATABASE_FILE`) e carrega o seed automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Configuração

Nenhum segredo fica no código: tudo vem de variável de ambiente, documentada em
`.env.example` (o `.env` está no `.gitignore`).

Com `NODE_ENV=production`, a ausência de `PAYMENT_GATEWAY_KEY` ou `ADMIN_API_KEY`
derruba o boot. Fora de produção a aplicação sobe com valores de desenvolvimento
e registra um `warn` nomeando cada variável ausente.

## Endpoints

| Método | Rota | Autenticação |
|---|---|---|
| `POST` | `/api/checkout` | pública |
| `GET` | `/api/admin/financial-report` | header `X-Admin-Api-Key` |
| `DELETE` | `/api/users/:id` | header `X-Admin-Api-Key` |

O relatório financeiro aceita `?page=` e `?per_page=` (máximo 100) e devolve a
paginação nos headers `X-Total-Count`, `X-Page` e `X-Per-Page` — o corpo continua
sendo o array do contrato original.

O `POST /api/checkout` aceita tanto os nomes de campo originais (`usr`, `eml`,
`pwd`, `c_id`, `card`) quanto os nomes por extenso (`userName`, `email`,
`password`, `courseId`, `cardNumber`). A senha passou a ser obrigatória, com no
mínimo 8 caracteres.

## Arquitetura

```
src/
├── config/           # variáveis de ambiente e constantes de domínio
├── domain/           # erros de domínio
├── infrastructure/   # banco, migrations, logger, hashing, gateway de pagamento
├── models/           # repositórios: um por entidade, queries parametrizadas
├── services/         # regra de negócio, transações — não conhecem HTTP
├── controllers/      # entrada validada → service → resposta
├── routes/           # rota → middleware → controller
├── middlewares/      # error handler central, validação, autorização, paginação
├── schemas/          # schemas de validação (zod)
├── app.js            # composition root: buildApp(deps)
└── server.js         # entry point
```

`buildApp({ db, paymentGateway, logger })` permite montar a aplicação inteira com
dublês, sem banco nem gateway reais.

O relatório da auditoria que originou esta refatoração está em
`reports/audit-project-2.md`, na raiz do repositório.
