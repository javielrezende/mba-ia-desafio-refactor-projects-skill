# Relatório de Auditoria Arquitetural — ecommerce-api-legacy

| | |
|---|---|
| **Projeto** | ecommerce-api-legacy |
| **Stack** | Node.js 24 + Express 4 (^4.18.2, lock 4.22.1) + sqlite3 ^5.1.6 |
| **Domínio** | LMS com fluxo de checkout (usuários, cursos, matrículas, pagamentos, audit log) |
| **Arquitetura anterior** | God Class — `AppManager` (141 linhas) concentrando conexão, DDL, seed, roteamento e regra de negócio |
| **Arquivos analisados** | 3 (180 linhas) |
| **Endpoints** | 3 rotas |
| **Auth** | 0 de 3 rotas exigem credencial — nenhum middleware de autenticação no projeto |
| **Data** | 2026-08-22 |
| **Skill** | refactor-arch v1 |

> O diretório se chama `ecommerce-api-legacy`, mas as tabelas (`courses`, `enrollments`)
> e as rotas (`/api/checkout` de curso) descrevem um **LMS**, não um e-commerce — o
> README e o log de boot ("Frankenstein LMS") confirmam.

## Resumo

| Severidade | Qtd. |
|---|---|
| CRITICAL | 5 |
| HIGH | 5 |
| MEDIUM | 3 |
| LOW | 4 |
| **Total** | **17** |

## Findings

### [CRITICAL] 1. God Class / God Module

- **Anti-pattern:** AP-03
- **Arquivo(s):** `src/AppManager.js:1-141`

**Descrição**

`AppManager` acumula **8 das 8** responsabilidades da heurística do catálogo:
conexão de banco (`:7`), DDL (`:12-16`), seed (`:18-21`), roteamento HTTP
(`:28`, `:80`, `:131`), validação de entrada (`:35`), regra de negócio de
pagamento (`:46`), acesso a dados (todas as queries) e serialização de saída
(`:60`, `:112-115`).

**Impacto**

Nenhuma regra é alcançável sem subir Express e SQLite juntos. Não há um único
ponto do fluxo de checkout testável em isolamento, e qualquer mudança tem raio
de alcance sobre a aplicação inteira.

**Recomendação**

Quebrar em `config/`, `models/`, `services/`, `controllers/`, `routes/`. → RP-03

---

### [CRITICAL] 2. Hardcoded Credentials and Secrets

- **Anti-pattern:** AP-02
- **Arquivo(s):** `src/utils.js:1-7`

**Descrição**

```js
const config = {
    dbUser: "admin_master",
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
    smtpUser: "no-reply@fullcycle.com.br",
    port: 3000
};
```

Não havia `.env`, `.env.example` nem `dotenv` no manifesto.

**Impacto**

O prefixo `pk_live_` indica credencial de produção. O valor está versionado no
histórico do Git — rotacionar não remove o commit, e qualquer clone do
repositório carrega o segredo.

**Recomendação**

Mover para variáveis de ambiente com `.env.example` versionado. **As credenciais
expostas precisam ser rotacionadas**, não apenas removidas do código. → RP-02

---

### [CRITICAL] 3. Sensitive Data Exposure — cartão e chave de gateway em log

- **Anti-pattern:** AP-05 (agravando AP-17)
- **Arquivo(s):** `src/AppManager.js:45`

**Descrição**

```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```

Confirmado na execução da linha de base:
`Processando cartão 4111222233334444 na chave pk_live_1234567890abcdef`.

**Impacto**

Todo coletor de log (arquivo, stdout do Docker, CloudWatch) passa a armazenar o
PAN completo em claro — violação direta de PCI-DSS — e a chave de produção do
gateway vaza pelo mesmo canal, a cada checkout.

**Recomendação**

Remover a linha; logar apenas o cartão mascarado e o identificador da
transação. → RP-02, RP-13

---

### [CRITICAL] 4. Broken Authentication / Weak Password Hashing

- **Anti-pattern:** AP-04
- **Arquivo(s):** `src/utils.js:17-23`, `src/AppManager.js:68`

**Descrição**

```js
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```

Criptografia caseira: concatena 10.000 vezes os 2 primeiros caracteres do base64
da senha e devolve os 10 primeiros caracteres do resultado. Sem salt e
determinística. Em `AppManager.js:68`, quando o campo de senha vem vazio o
servidor preenche silenciosamente com `"123456"`:

```js
let hash = badCrypto(p || "123456");
```

**Impacto**

O hash de qualquer senha depende **apenas dos 2 primeiros caracteres do seu
base64** — o espaço de saída colapsa e a reversão é trivial. Senhas iguais geram
hashes iguais. Contas criadas sem senha ficam acessíveis com um valor conhecido,
sem o usuário saber.

**Recomendação**

KDF com salt por senha (scrypt/bcrypt/argon2); senha obrigatória, nunca
default. → RP-04

---

### [CRITICAL] 5. Sensitive Data Exposure — endpoints admin e destrutivo sem autenticação

- **Anti-pattern:** AP-05
- **Arquivo(s):** `src/AppManager.js:80`, `src/AppManager.js:131`

**Descrição**

`GET /api/admin/financial-report` devolve receita por curso, nome de cada aluno
e valor pago, sem nenhuma verificação de identidade.
`DELETE /api/users/:id` apaga qualquer usuário por id, também sem autenticação.
Não existe middleware de autenticação em nenhum arquivo do projeto.

**Impacto**

Qualquer pessoa com acesso à rede lê o faturamento e a base de alunos e apaga
usuários arbitrariamente com um único `curl`.

**Recomendação**

Middleware de autorização aplicado às rotas administrativas. → RP-04

---

### [HIGH] 6. Business Logic Inside Controller / Route

- **Anti-pattern:** AP-06
- **Arquivo(s):** `src/AppManager.js:28-78` (checkout, 51 linhas), `:80-129` (relatório, 50 linhas)

**Descrição**

Os handlers HTTP fazem tudo no mesmo corpo: leem `req.body`, validam, executam
SQL, decidem a aprovação do pagamento, gravam matrícula, pagamento e auditoria e
montam a resposta. A regra de aprovação está literalmente dentro do callback da
rota:

```js
let status = cc.startsWith("4") ? "PAID" : "DENIED";
```

Não existe camada de serviço no projeto.

**Impacto**

A regra de aprovação de pagamento e o cálculo de receita só existem dentro de um
request HTTP — não dá para reusá-los em job, CLI ou worker, nem testá-los sem
subir servidor e banco.

**Recomendação**

Extrair `CheckoutService` e `ReportService` puros, sem `req`/`res`. → RP-05

---

### [HIGH] 7. Multi-Step Write Without Transaction

- **Anti-pattern:** AP-09
- **Arquivo(s):** `src/AppManager.js:50-63`, `:12-16`, `:131-137`

**Descrição**

O checkout faz 4 escritas dependentes (usuário → matrícula → pagamento → audit
log) sem `BEGIN`/`COMMIT`/`ROLLBACK`. Nenhuma `CREATE TABLE` (`:12-16`) declara
`FOREIGN KEY`, e não há `PRAGMA foreign_keys = ON`. O `DELETE` de usuário
responde, literalmente:

```js
res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
```

**Impacto**

Falha no `INSERT` de pagamento deixa o aluno matriculado sem ter pago, e o
cliente recebe 500 como se nada tivesse sido gravado. O `DELETE` produz órfãos
por desenho — confirmado na linha de base: após `DELETE /api/users/1`, o
relatório passou a exibir `{"student":"Unknown","paid":997}`.

**Recomendação**

Envolver o fluxo em transação com rollback; declarar FKs e habilitar o
pragma. → RP-09

---

### [HIGH] 8. Tight Coupling / No Dependency Injection

- **Anti-pattern:** AP-07
- **Arquivo(s):** `src/AppManager.js:7`, `src/AppManager.js:2`, `src/app.js:8-10`

**Descrição**

```js
constructor() {
    this.db = new sqlite3.Database(':memory:');
}
```

A classe que usa o banco também o instancia. `app.js` apenas faz
`new AppManager()` — nada é injetado. `utils.js` (config, cache, crypto) é
importado diretamente por `AppManager` (`:2`).

**Impacto**

Não há como substituir o banco por um dublê em teste, nem trocar SQLite por
Postgres, sem reescrever a classe. Viola inversão de dependência.

**Recomendação**

Conexão criada no composition root e injetada. → RP-06

---

### [HIGH] 9. Swallowed / Absent Error Handling

- **Anti-pattern:** AP-10
- **Arquivo(s):** `src/AppManager.js:57`, `:92`, `:104`, `:106`, `:133`; contadores em `:86`, `:93`

**Descrição**

16 callbacks recebem `err`, apenas 6 o checam. Sub-itens:

1. `:133` — o `DELETE` ignora `err` e responde sucesso em qualquer cenário.
2. `:104`/`:106` — erros do relatório viram `undefined` e são serializados como
   `'Unknown'` / `0`: dado errado entregue como se fosse válido.
3. `:92` — `enrollments.length` sobre `undefined` em callback assíncrono lança
   `TypeError` fora de qualquer `try/catch` alcançável e derruba o processo Node.
4. `:86`/`:93` — contadores manuais `coursesPending`/`enrPending` decrementados
   dentro de `forEach`: o `push` acontece na ordem de conclusão das queries, não
   na ordem da lista de origem, e não há `ORDER BY` — o mesmo request pode
   devolver os cursos em ordens diferentes.
5. Nenhum `app.use((err, req, res, next))` registrado em todo o projeto.

**Impacto**

Bug invisível em produção (sem stack trace em lugar nenhum), resposta não
determinística e queda do processo inteiro por um erro de banco.

**Recomendação**

Migrar de callback para Promise/async-await e registrar error handler
central. → RP-10, RP-14

---

### [HIGH] 10. Mutable Global State

- **Anti-pattern:** AP-08
- **Arquivo(s):** `src/utils.js:9-10`, `:12-15`, `:25`

**Descrição**

```js
let globalCache = {};
let totalRevenue = 0;

function logAndCache(key, data) {
    console.log(`[LOG] Salvando no cache: ${key}`);
    globalCache[key] = data;
}
module.exports = { config, logAndCache, badCrypto, globalCache, totalRevenue };
```

`logAndCache` é chamado a cada checkout (`AppManager.js:59`) e escreve em
`globalCache` sem TTL nem limite de tamanho.

**Impacto**

O cache cresce indefinidamente entre requisições — vazamento de memória — e o
estado compartilhado torna o resultado dependente de ordem entre requests.
Agravante de CommonJS: `totalRevenue` é primitivo, então `module.exports`
congela uma **cópia** do valor; qualquer incremento interno jamais seria visto
por quem importou.

**Recomendação**

Eliminar o estado de módulo; acumuladores viram consulta ao banco. → RP-07

---

### [MEDIUM] 11. N+1 Query

- **Anti-pattern:** AP-11
- **Arquivo(s):** `src/AppManager.js:83-127` (laços em `:89` e `:102`)

**Descrição**

O relatório dispara 1 query de cursos, 1 query de matrículas por curso e 2
queries (usuário + pagamento) por matrícula, em `forEach` aninhado de dois
níveis. Fórmula: `1 + N + 2*(N*M)`.

Com 20 cursos × 30 matrículas: **1.221 queries por request**.

**Impacto**

A latência cresce linearmente com a base. Como não existe índice nas chaves
estrangeiras (nem FKs — ver finding 7), cada uma dessas queries é um full table
scan.

**Recomendação**

Colapsar em uma única query com `JOIN` e criar índices nas FKs. → RP-08

---

### [MEDIUM] 12. Missing / Superficial Input Validation

- **Anti-pattern:** AP-14
- **Arquivo(s):** `src/AppManager.js:29-35`, `:132`

**Descrição**

```js
if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");
```

Validação apenas de presença: sem formato de e-mail, sem tipo de `c_id`, sem
formato de cartão. `pwd` (`:31`) não é validado nem exigido — cai no default
silencioso do finding 4. `req.params.id` (`:132`) vai direto para o SQL sem
checagem de tipo. Nenhuma biblioteca de schema no manifesto.

**Impacto**

`cc.startsWith(...)` em `:46` lança `TypeError` se `card` vier como número; em
callback assíncrono isso derruba o processo Node inteiro.

**Recomendação**

Middleware de validação por schema, aplicado antes do controller. → RP-11

---

### [MEDIUM] 13. Listing Without Pagination

- **Anti-pattern:** AP-12
- **Arquivo(s):** `src/AppManager.js:83`

**Descrição**

`SELECT * FROM courses` sem `LIMIT`/`OFFSET`, e o relatório varre todas as
matrículas e todos os pagamentos de todos os cursos, sem filtro de período e sem
parâmetros `page`/`limit`.

**Impacto**

A resposta cresce junto com a tabela, sem teto — funciona com o seed de 2 cursos
e derruba a aplicação com dezenas de milhares de matrículas.

**Recomendação**

`LIMIT`/`OFFSET` com teto, mantendo o formato de resposta. → RP-16

---

### [LOW] 14. Magic Numbers and Domain String Literals

- **Anti-pattern:** AP-16
- **Arquivo(s):** `src/utils.js:19`, `:20`, `:22`; `src/AppManager.js:46`, `:68`, `:19-21`

**Descrição**

`10000` iterações, `substring(0, 2)` e `substring(0, 10)` em `badCrypto`; `"4"`
como prefixo que decide a aprovação do cartão (`:46`); `"123456"` como senha
padrão (`:68`); `'PAID'`/`'DENIED'` como literais soltos; preços `997.00`/`497.00`
no seed.

**Impacto**

A regra "cartão começando com 4 é aprovado" é invisível a quem lê o handler, e
mudar o conjunto de status exige caçar strings pelo arquivo.

**Recomendação**

Constantes nomeadas em `config/constants.js`. → RP-12

---

### [LOW] 15. console.log as Logging Mechanism

- **Anti-pattern:** AP-17
- **Arquivo(s):** `src/utils.js:13`, `src/app.js:13`

**Descrição**

`console.log` é o único mecanismo de log do projeto — sem nível, sem timestamp e
sem destino configurável. A terceira ocorrência (`AppManager.js:45`) está
reportada como CRITICAL no finding 3, por imprimir cartão e chave live.

**Impacto**

Não há como silenciar, filtrar por severidade ou direcionar o log em produção.

**Recomendação**

Logger estruturado com nível, injetado nas camadas. → RP-13

---

### [LOW] 16. Poor Naming

- **Anti-pattern:** AP-18
- **Arquivo(s):** `src/AppManager.js:26`, `:29-33`, `:54`, `:57`; `src/utils.js:12`

**Descrição**

Variáveis de uma letra em um handler de 51 linhas (`u`, `e`, `p`, `cid`, `cc`) —
`e` é especialmente perigoso em JS, por ser a convenção universal de `error`.
Abreviações `usr`/`eml`/`pwd`/`c_id` no **contrato público** da API
(`api.http:8-13`). `logAndCache` tem "and" no nome, denunciando duas
responsabilidades. `const self = this` (`:26`) convive com arrow functions,
necessário só porque `function(err)` em `:50`/`:54` faz rebind de `this`.

**Impacto**

Renomear os campos do payload seria breaking change para os clientes existentes.

**Recomendação**

Nomes por extenso internamente; no payload público, aceitar os dois nomes
durante a transição. → RP-15

---

### [LOW] 17. Dead Code / Dead Layer

- **Anti-pattern:** AP-19
- **Arquivo(s):** `src/AppManager.js:2`, `src/utils.js:9-10`, `:14`, `:25`

**Descrição**

`totalRevenue` é importado em `AppManager.js:2` e nunca referenciado no arquivo.
`globalCache` é escrito por `logAndCache` (`:14`) e **nunca lido em lugar
nenhum** — a funcionalidade de cache não existe, apenas consome memória. Ambos
são exportados em `:25` sem consumidor real.

**Impacto**

O leitor seguinte acredita que existe cache e acumulador de receita funcionando;
não existe nenhum dos dois.

**Recomendação**

Remover os símbolos mortos. → RP-15

---

## APIs deprecated

**Nenhuma ocorrência encontrada.**

Varredura executada sobre `src/`: `new Buffer()`, `url.parse()`, `.substr()`,
`crypto.createCipher()`, `require('request')`, `util.isArray`, `app.del()`,
`req.param()`, `res.send(status, body)` — 0 matches.

Observação fora da tabela de depreciações: `express` e `sqlite3` estavam
declarados em faixa `^` não fixada (`^4.18.2` / `^5.1.6`), com o lock resolvendo
4.22.1 e 5.1.7.

## Cobertura da varredura

Anti-patterns verificados: **19/19**.

Ausentes neste projeto:

- **AP-01** (SQL Injection) — as 12 queries do projeto usam placeholders `?`
  com os valores no segundo argumento; nenhuma concatenação encontrada.
- **AP-13** (duplicação de regra de negócio) — cada regra aparece uma única vez
  no código.
- **AP-15** (API deprecated) — ver seção acima.

---

## Resultado da Refatoração

### Estrutura antes → depois

**Antes** (3 arquivos, 180 linhas)

```
src/
├── AppManager.js   (141 linhas — God Class)
├── app.js          (14 linhas)
└── utils.js        (25 linhas)
```

**Depois** (29 arquivos, 1.024 linhas)

```
src/
├── config/
│   ├── index.js                    # variáveis de ambiente, sem literal
│   └── constants.js                # constantes de domínio
├── domain/
│   └── errors.js                   # DomainError, ValidationError, NotFoundError,
│                                   # PaymentDeclinedError, UnauthorizedError
├── infrastructure/
│   ├── database.js                 # conexão promisificada + transaction()
│   ├── migrations.js               # DDL com FK/índices + seed
│   ├── logger.js                   # logger estruturado com nível
│   ├── passwordHasher.js           # scrypt + salt (crypto nativo)
│   └── paymentGateway.js           # interface + gateway fake, cartão mascarado
├── models/
│   ├── userRepository.js
│   ├── courseRepository.js
│   ├── enrollmentRepository.js
│   ├── paymentRepository.js
│   ├── auditLogRepository.js
│   └── reportRepository.js         # a query com JOIN que substituiu o N+1
├── services/
│   ├── checkoutService.js          # regra do checkout, dentro de transação
│   ├── reportService.js
│   └── userService.js
├── controllers/
│   ├── checkoutController.js       # 5 linhas
│   ├── reportController.js         # 10 linhas
│   └── userController.js           # 5 linhas
├── routes/
│   └── index.js                    # rota → middleware → controller
├── middlewares/
│   ├── errorHandler.js             # error handler central + asyncHandler
│   ├── validate.js
│   ├── adminAuth.js
│   └── pagination.js
├── schemas/
│   ├── checkoutSchema.js
│   └── userSchema.js
├── app.js                          # composition root: buildApp(deps)
└── server.js                       # entry point
.env.example                        # versionado, com valores fake
```

`src/AppManager.js` e `src/utils.js` foram removidos após a migração integral.
O `package.json` passou a apontar `main`/`start` para `src/server.js`, e o README
foi atualizado — `npm start` continua sendo o comando de boot.

### Findings resolvidos

| # | Severidade | Finding | Status | Onde foi resolvido |
|---|---|---|---|---|
| 1 | CRITICAL | God Class | ✅ Resolvido | `AppManager` desmembrado em 29 arquivos; maior arquivo do projeto tem 89 linhas |
| 2 | CRITICAL | Segredos hardcoded | ✅ Resolvido | `src/config/index.js` lê tudo de `process.env`; `.env.example` versionado; varredura AP-02 limpa |
| 3 | CRITICAL | Cartão e chave em log | ✅ Resolvido | `src/infrastructure/paymentGateway.js:9-12` — `maskCard()`; log mostra `**** **** **** 4444`, chave nunca é logada |
| 4 | CRITICAL | Hashing fraco / senha default | ✅ Resolvido | `src/infrastructure/passwordHasher.js` — scrypt com salt aleatório; senha obrigatória, mínimo 8 caracteres |
| 5 | CRITICAL | Endpoints admin sem auth | ✅ Resolvido | `src/middlewares/adminAuth.js` aplicado às duas rotas em `src/routes/index.js:24,31` |
| 6 | HIGH | Regra no controller | ✅ Resolvido | `src/services/checkoutService.js`, `reportService.js`; controllers com 5-10 linhas, sem SQL |
| 7 | HIGH | Escrita sem transação | ✅ Resolvido | `src/infrastructure/database.js:44-57` (BEGIN/COMMIT/ROLLBACK) + FKs `ON DELETE CASCADE` e `PRAGMA foreign_keys = ON` em `migrations.js` |
| 8 | HIGH | Sem injeção de dependência | ✅ Resolvido | `src/app.js` é o único ponto que constrói o concreto; `buildApp({db, paymentGateway, logger})` aceita dublês |
| 9 | HIGH | Erro engolido / contador manual | ✅ Resolvido | Driver promisificado; `src/middlewares/errorHandler.js` registrado por último; contadores eliminados junto com os callbacks aninhados |
| 10 | HIGH | Estado global mutável | ✅ Resolvido | `globalCache` e `totalRevenue` removidos; varredura AP-08 limpa |
| 11 | MEDIUM | Query N+1 | ✅ Resolvido | `src/models/reportRepository.js` — 1 query com `JOIN` + `ORDER BY` no lugar de `1 + N + 2*(N*M)`; índices nas FKs |
| 12 | MEDIUM | Validação ausente | ✅ Resolvido | `src/schemas/` (zod) + `src/middlewares/validate.js`; cartão como número agora responde 200 em vez de derrubar o processo |
| 13 | MEDIUM | Sem paginação | ✅ Resolvido | `src/middlewares/pagination.js` (teto de 100) + `LIMIT`/`OFFSET`; corpo continua array puro, paginação em headers |
| 14 | LOW | Magic numbers | ✅ Resolvido | `src/config/constants.js` — `PaymentStatus`, `APPROVED_CARD_PREFIX`, `MIN_PASSWORD_LENGTH`, tetos de paginação |
| 15 | LOW | console.log como log | ✅ Resolvido | `src/infrastructure/logger.js` injetado; 0 `console.log` em `src/` |
| 16 | LOW | Nomenclatura | ⚠️ Parcial | Nomes internos por extenso e `self = this` eliminado. As abreviações do **payload público** foram mantidas por compatibilidade: `checkoutSchema.js` aceita `usr`/`eml`/`pwd`/`c_id`/`card` **e** `userName`/`email`/`password`/`courseId`/`cardNumber` |
| 17 | LOW | Código morto | ✅ Resolvido | `globalCache`, `totalRevenue`, `logAndCache` e `badCrypto` removidos com `utils.js` |

Todos os findings CRITICAL e HIGH foram resolvidos.

### Validação

| Verificação | Resultado |
|---|---|
| Aplicação sobe sem erro | ✅ `npm start` — boot limpo, sem stack trace |
| Endpoints originais respondem | ✅ 7/7 chamadas da linha de base com o mesmo status e a mesma forma de resposta |
| Varredura final do catálogo | ✅ 0 anti-patterns CRITICAL/HIGH remanescentes |
| Matriz de acesso | ✅ 3/3 rotas conferidas pela chamada; 0 rota sensível anônima |

### Matriz de acesso por rota

Conferida em 2026-09-01 com a aplicação nos **defaults versionados** (sem `.env`
local — o `warn` de boot confirma que a chave usada é a de desenvolvimento).
Uma linha por rota registrada em `src/routes/index.js`: **3 rotas, 3 linhas**.

| Rota | Classe | Anônimo | Chave errada | Chave admin | Observação |
|---|---|---|---|---|---|
| `POST /api/checkout` | público | 200 | 200 | 200 | é a rota de matrícula + criação da conta do aluno: exigir credencial aqui impediria qualquer venda, do mesmo modo que `POST /users` num sistema com registro. Não devolve dado de terceiros e nem lista nada — cria o próprio registro do chamador |
| `GET /api/admin/financial-report` | privilegiado | **401** | **401** | 200 | faturamento por curso e nome dos alunos pagantes |
| `DELETE /api/users/:id` | privilegiado | **401** | **401** | 200 | remoção destrutiva, com cascata em matrículas e pagamentos |

```
POST   /api/checkout                anon=200 comKey=200
GET    /api/admin/financial-report  anon=401 comKey=200
DELETE /api/users/1                 anon=401 comKey=200
GET    /api/admin/financial-report  (chave errada)  401
DELETE /api/users/2                 (chave errada)  401

$ curl -s localhost:3000/api/admin/financial-report
Não autorizado
```

A comparação da chave é feita com `crypto.timingSafeEqual` (`middlewares/adminAuth.js`),
depois de conferir o comprimento — não vaza o prefixo correto pelo tempo de resposta.
Não existe variável que desligue o guard: `ADMIN_API_KEY` escolhe *qual* chave vale,
e em `NODE_ENV=production` a ausência dela **derruba o boot** em vez de subir com o
valor de desenvolvimento.

**Comparação linha de base → refatorado** (saída real do `curl`):

| # | Chamada | Antes | Depois |
|---|---|---|---|
| 1 | `POST /api/checkout` (sucesso) | `200` · `{"msg":"Sucesso","enrollment_id":2}` | `200` · `{"msg":"Sucesso","enrollment_id":2}` |
| 2 | `POST /api/checkout` (recusado) | `400` · `Pagamento recusado` | `400` · `Pagamento recusado` |
| 3 | `POST /api/checkout` (campo faltando) | `400` · `Bad Request` | `400` · `Bad Request` |
| 4 | `POST /api/checkout` (curso inexistente) | `404` · `Curso não encontrado` | `404` · `Curso não encontrado` |
| 5 | `GET /api/admin/financial-report` | `200` · `[{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]},{"course":"Docker",...}]` | `200` · corpo idêntico + headers `X-Total-Count: 2`, `X-Page: 1`, `X-Per-Page: 20` |
| 6 | `DELETE /api/users/1` | `200` · texto | `200` · texto (mensagem alterada — ver breaking changes) |
| 7 | `GET /api/admin/financial-report` (pós-delete) | `200` · `{"student":"Unknown","paid":997}` (registro órfão) | `200` · `{"course":"Clean Architecture","revenue":0,"students":[]}` (cascata) |

Log de boot da aplicação refatorada:

```
{"time":"2026-08-22T21:18:55.406Z","level":"warn","msg":"variáveis sensíveis ausentes: usando valores de desenvolvimento (ver .env.example)","variables":["PAYMENT_GATEWAY_KEY","ADMIN_API_KEY"]}
{"time":"2026-08-22T21:18:55.408Z","level":"info","msg":"LMS API no ar","port":3000,"env":"development"}
```

Log de um checkout — cartão mascarado, chave do gateway ausente:

```
{"time":"2026-08-22T21:18:58.311Z","level":"info","msg":"cobrança processada","card":"**** **** **** 4444","amount":497,"status":"PAID"}
{"time":"2026-08-22T21:18:58.312Z","level":"info","msg":"checkout concluído","userId":2,"courseId":2,"enrollmentId":2,"course":"Docker"}
```

Teste do defeito que derrubava o processo (`card` enviado como número):

```
POST /api/checkout {"card":4111222233334444}  →  200 {"msg":"Sucesso","enrollment_id":3}
GET  /api/admin/financial-report              →  200   (processo continua vivo)
```

Varredura final do catálogo sobre `src/`:

```
AP-01 SQL Injection ............ 0 matches
AP-02 Segredos hardcoded ....... 0 matches
AP-04 Crypto fraca ............. 0 matches (apenas 1 menção em comentário)
AP-05 Dado sensível em log ..... 0 matches (log usa maskCard)
AP-07 new sqlite3.Database ..... 1 match — infrastructure/database.js, chamado pelo composition root
AP-08 Estado global mutável .... 0 matches
AP-09 BEGIN/COMMIT/ROLLBACK .... presentes; FK + PRAGMA foreign_keys presentes
AP-10 Contador manual .......... 0 matches; error handler central registrado
AP-11 Query dentro de laço ..... 0 matches
AP-15 API deprecated ........... 0 matches
AP-17 console.log .............. 0 matches
Maior arquivo do projeto ....... 89 linhas (src/app.js)
```

### Breaking changes

Mudanças de contrato, todas decorrentes de correções de segurança e integridade:

1. **`GET /api/admin/financial-report` passou a exigir autenticação.** Sem o
   header `X-Admin-Api-Key` a resposta é `401 Não autorizado`. Correção do
   finding 5 — o relatório expunha faturamento e nomes de alunos publicamente.
2. **`DELETE /api/users/:id` passou a exigir autenticação** pelo mesmo header, e
   um `:id` não numérico agora responde `400 Bad Request` em vez de `200`.
   Correção dos findings 5 e 12.
3. **`POST /api/checkout` passou a exigir senha com no mínimo 8 caracteres.**
   Antes, senha ausente era substituída silenciosamente por `"123456"` e
   qualquer tamanho era aceito. Correção do finding 4. O exemplo de "pagamento
   recusado" do `api.http` foi atualizado para uma senha válida.
4. **`POST /api/checkout` passou a validar o formato de e-mail e do cartão**
   (13-19 dígitos). Payloads malformados que antes eram aceitos agora respondem
   `400 Bad Request`. Correção do finding 12.
5. **A mensagem do `DELETE /api/users/:id` mudou** de
   `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."`
   para `"Usuário deletado."` — a afirmação deixou de ser verdadeira: as
   matrículas e pagamentos agora são removidos em cascata. Status e tipo de
   resposta (`200`, texto) preservados. Correção do finding 7.

Mudanças **compatíveis** (sem quebra):

- O `POST /api/checkout` aceita tanto os nomes de campo originais quanto os
  nomes por extenso.
- A paginação do relatório vai em headers; o corpo continua sendo o array puro.
- Após um checkout recusado, o usuário deixa de ser persistido (rollback da
  transação). Não observável pela API — não há endpoint de listagem de usuários.

### Dependências adicionadas

| Pacote | Versão | Para quê |
|---|---|---|
| `zod` | ^4.4.3 | Schemas de validação de entrada (finding 12) |
| `dotenv` | ^17.4.2 | Carregar `.env` em desenvolvimento (finding 2) |

O hashing de senha e a comparação em tempo constante usam apenas o módulo
`node:crypto` nativo — nenhuma dependência extra.

### Limitações conhecidas

- **Segredos rotacionados:** `pk_live_1234567890abcdef` e
  `senha_super_secreta_prod_123` continuam no histórico do Git. Removê-los do
  código não basta — se forem credenciais reais, precisam ser rotacionadas no
  provedor.
- **Transação e concorrência:** `db.transaction()` usa uma única conexão SQLite e
  não é reentrante — checkouts simultâneos são serializados pelo driver. Para um
  banco com pool (Postgres/MySQL), a transação deve passar a usar uma conexão
  dedicada por fluxo.
- **Autorização por API key:** o `adminAuth` valida uma chave compartilhada, não
  identidade de usuário. É o suficiente para fechar o buraco do finding 5; um
  modelo de papéis por usuário fica como evolução.
