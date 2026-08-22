# Relatório de Auditoria Arquitetural — code-smells-project

| | |
|---|---|
| **Projeto** | code-smells-project |
| **Stack** | Python 3.12 + Flask 3.1.1 |
| **Domínio** | API de E-commerce (produtos, usuários/autenticação, pedidos com itens e baixa de estoque, relatório de vendas) |
| **Arquitetura anterior** | Camadas nominais vazando — `app.py`/`controllers.py`/`models.py`/`database.py`, com regra de negócio no model e SQL no arquivo de rotas |
| **Arquivos analisados** | 4 (780 linhas) |
| **Data** | 2026-08-17 |
| **Skill** | refactor-arch v1 |

## Resumo

| Severidade | Qtd. |
|---|---|
| CRITICAL | 5 |
| HIGH | 5 |
| MEDIUM | 4 |
| LOW | 4 |
| **Total** | **18** |

## Findings

### [CRITICAL] 1. SQL Injection — queries montadas por concatenação

- **Anti-pattern:** AP-01
- **Arquivo(s):** `models.py:28`, `:48-49`, `:110`, `:291-297` (+18 ocorrências no total)

**Descrição**

22 queries montadas por concatenação de string. O login concatena e-mail e senha direto no `SELECT`:

```python
cursor.execute(
    "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
)
```

`buscar_produtos` (`models.py:289-299`) monta a cláusula `WHERE` inteira por concatenação. O próprio `database.py:70-83` usa placeholders `?` no seed — a forma correta estava disponível e foi ignorada.

**Impacto**

`POST /login {"email": "x' OR '1'='1' --"}` autentica sem senha. Leitura arbitrária da tabela `usuarios` (que guardava senha em texto puro) via `/produtos/busca?q=`, e destruição de dados via `DELETE /produtos/<id>`.

**Recomendação**

Parametrizar 100% das queries, com os curingas do `LIKE` dentro do valor. → RP-01

---

### [CRITICAL] 2. Exposição de dado sensível

- **Anti-pattern:** AP-05
- **Arquivo(s):** `models.py:83`, `:99`; `controllers.py:285-289`; `app.py:47-57`, `:59-78`

**Descrição**

- `GET /usuarios` e `GET /usuarios/<id>` devolviam o campo `senha` em texto puro.
- `GET /health` devolvia `"secret_key": "minha-chave-super-secreta-123"`, `debug` e `db_path`.
- `POST /admin/query` executava SQL arbitrário vindo do corpo, sem autenticação.
- `POST /admin/reset-db` apagava as quatro tabelas, sem autenticação.
- Todo handler devolvia `str(e)` da exceção no corpo do 500.

**Impacto**

`/admin/query` não era sequer injeção — era um console de banco público. `/health` entregava a chave de assinatura de sessão a qualquer requisição anônima.

**Recomendação**

Remover o campo sensível da serialização, remover os endpoints `/admin/*`, enxugar `/health` e centralizar o erro sem vazar detalhe. → RP-02, RP-04

---

### [CRITICAL] 3. Credenciais e segredos hardcoded

- **Anti-pattern:** AP-02
- **Arquivo(s):** `app.py:7-9`, `:88`; `controllers.py:289`; `database.py:5`

**Descrição**

`SECRET_KEY = "minha-chave-super-secreta-123"` fixa no código e repetida no `/health`; `DEBUG = True`; `app.run(host="0.0.0.0", port=5000, debug=True)`; `CORS(app)` sem restrição de origem; `db_path = "loja.db"` fixo. Nenhuma variável de ambiente no projeto.

**Impacto**

O segredo está versionado no histórico do Git — rotacionar o valor não apaga o commit. `debug=True` com `host=0.0.0.0` expõe o console interativo do Werkzeug na rede, que executa Python arbitrário. CORS aberto permite que qualquer site chame a API com as credenciais do navegador.

**Recomendação**

`config/settings.py` lendo `os.environ`, `.env.example` versionado, segredo obrigatório que falha o boot quando ausente. → RP-02

---

### [CRITICAL] 4. Autenticação quebrada / hashing de senha ausente

- **Anti-pattern:** AP-04
- **Arquivo(s):** `models.py:105-120`, `:122-131`; `database.py:75-83`; `controllers.py:167-186`

**Descrição**

Senha gravada em texto puro, inclusive no seed (`"admin123"`, `"123456"`). O login comparava a senha dentro do SQL — sem hash e sem salt. O login bem-sucedido devolvia apenas o dicionário do usuário: não havia token, sessão nem verificação de autorização em nenhum endpoint, incluindo `/admin/*`.

**Impacto**

Vazamento do banco entregaria todas as senhas em claro. O campo `tipo: 'admin'` existia no schema e nunca era consultado: qualquer anônimo resetava o banco e lia o relatório de faturamento.

**Recomendação**

Hash com `werkzeug.security` (scrypt), comparação em Python, política mínima de senha e caminho de login com custo constante. → RP-04

---

### [CRITICAL] 5. God Module

- **Anti-pattern:** AP-03
- **Arquivo(s):** `models.py:1-314`; `database.py:7-86`; `app.py:47-78`

**Descrição**

`models.py` acumulava quatro responsabilidades do catálogo para quatro domínios distintos: acesso a dados, regra de negócio (faixas de desconto em `:256-262`, cálculo de total e baixa de estoque em `:137-167`), serialização repetida oito vezes e montagem de SQL. `database.py` acumulava conexão + DDL + seed. `app.py` acumulava roteamento + acesso direto ao banco.

**Impacto**

Não havia como testar a regra de desconto ou o cálculo do pedido sem subir o SQLite; qualquer alteração em produtos tocava o mesmo arquivo que atendia pedidos.

**Recomendação**

Quebrar em `models/` por entidade, `services/` para a regra e `controllers/` para orquestração. → RP-03

---

### [HIGH] 6. Regra de negócio dentro do controller / model — ausência de camada de serviço

- **Anti-pattern:** AP-06
- **Arquivo(s):** `controllers.py:24-62`, `:188-220`, `:237-255`, `:264-292`; `models.py:133-169`, `:235-273`

**Descrição**

Não existia camada de serviço. A regra estava dividida entre duas camadas erradas: validação de faixa e catálogo de categorias no controller; cálculo de total, checagem e baixa de estoque dentro do model; faixas de desconto dentro do model; transições de status válidas no controller. `health_check` executava quatro queries SQL direto no controller.

**Impacto**

A regra do pedido só era alcançável por requisição HTTP — não dava para reusá-la em job, CLI ou worker, nem testá-la sem servidor e banco.

**Recomendação**

Extrair services por domínio, sem `request`/`jsonify`. → RP-05

---

### [HIGH] 7. Acoplamento forte / ausência de injeção de dependência

- **Anti-pattern:** AP-07
- **Arquivo(s):** `database.py:10`; `models.py:1`, `:5`, `:25`, `:44` (+13 chamadas de `get_db()`); `controllers.py:3`, `:266`

**Descrição**

Toda função de `models.py` chamava `get_db()` importado do módulo de banco, e `controllers.py` também o importava direto. Nenhuma dependência era recebida por parâmetro ou construtor; a conexão SQLite era instanciada dentro do próprio módulo.

**Impacto**

Trocar o banco, ou usar um fake em teste, exigiria reescrever `models.py` inteiro. Viola inversão de dependência.

**Recomendação**

Repositórios e services recebendo dependências por construtor, montados num composition root. → RP-06

---

### [HIGH] 8. Estado global mutável

- **Anti-pattern:** AP-08
- **Arquivo(s):** `database.py:4-10`

**Descrição**

```python
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
```

**Impacto**

Uma única conexão SQLite compartilhada por todas as threads do servidor, com a proteção de thread do driver explicitamente desligada. Cursores e transações de requisições concorrentes se misturavam, e o `db.commit()` de uma requisição confirmava escritas parciais de outra.

**Recomendação**

Conexão por operação, criada por uma fábrica injetada. → RP-07

---

### [HIGH] 9. Escrita multi-passo sem transação

- **Anti-pattern:** AP-09
- **Arquivo(s):** `models.py:133-169`; `database.py:14-53` (sem `FOREIGN KEY`); `models.py:65-70`

**Descrição**

`criar_pedido` fazia um `INSERT` em `pedidos` e, por item, um `INSERT` em `itens_pedido` e um `UPDATE` de estoque — sem `BEGIN`/`ROLLBACK` e sem tratamento de falha no meio do laço. A checagem de estoque rodava num laço prévio, separada da baixa, abrindo janela de corrida. Nenhuma das quatro `CREATE TABLE` declarava `FOREIGN KEY`, e não havia `PRAGMA foreign_keys = ON`.

**Impacto**

Falha no item 3 de um pedido de 5 deixaria o pedido gravado com itens faltando e estoque debitado pela metade, com 500 para o cliente. `DELETE /produtos/<id>` deixava registros órfãos em `itens_pedido`.

**Recomendação**

Transação explícita envolvendo o fluxo inteiro, `FOREIGN KEY` no schema e `PRAGMA foreign_keys = ON` na abertura da conexão. → RP-09

---

### [HIGH] 10. Tratamento de erro espalhado e vazando exceção

- **Anti-pattern:** AP-10
- **Arquivo(s):** `controllers.py:10-12`, `:21-22`, `:60-62`, `:95-96` (+15 blocos); `app.py:47-57`, `:77-78`

**Descrição**

19 blocos `try/except Exception as e` copiados handler a handler, todos devolvendo `jsonify({"erro": str(e)}), 500` e nenhum registrando stack trace. Não havia `@app.errorhandler`. Erros de negócio eram sinalizados por dicionário com chave `"erro"` (`models.py:143`) e detectados por `if "erro" in resultado` (`controllers.py:205`) em vez de exceção tipada.

**Impacto**

O bug ficava invisível em produção — sem stack trace no log — e o detalhe interno da exceção ia para o cliente (nome de tabela, SQL malformado).

**Recomendação**

Exceções de domínio + error handler central com `logging`. → RP-10

---

### [MEDIUM] 11. Query N+1

- **Anti-pattern:** AP-11
- **Arquivo(s):** `models.py:171-201`, `:203-233`

**Descrição**

`get_pedidos_usuario` e `get_todos_pedidos` faziam uma query nos pedidos, mais uma query de itens por pedido (`:188`, `:220`), mais uma query de nome de produto por item (`:192`, `:224`) — laço aninhado em dois níveis, com cursores novos criados dentro do laço.

**Impacto**

100 pedidos × 5 itens = 1 + 100 + 500 = 601 queries num único `GET /pedidos`. Sem índice em `itens_pedido.pedido_id`, cada uma das 500 era um scan.

**Recomendação**

Uma query com `JOIN` entre `pedidos`, `itens_pedido` e `produtos`, agrupando em memória, com índices nas chaves estrangeiras. → RP-08

---

### [MEDIUM] 12. Duplicação de regra de negócio e de validação

- **Anti-pattern:** AP-13
- **Arquivo(s):** `controllers.py:24-62` vs `:64-96`; `models.py:4-22` vs `:24-41` vs `:285-314`; `models.py:171-201` vs `:203-233`

**Descrição**

- O bloco de validação de produto estava copiado entre `criar_produto` e `atualizar_produto` — **e já havia divergido**: o `POST` validava `len(nome)` entre 2 e 200 e a lista de categorias válidas; o `PUT` não validava nenhum dos dois.
- O dicionário de serialização de produto estava montado à mão três vezes; o de usuário, duas — com formas diferentes (só `login_usuario` omitia `senha`).
- `get_pedidos_usuario` e `get_todos_pedidos` eram o mesmo corpo de 30 linhas, diferindo apenas pelo `WHERE`.

**Impacto**

Era possível gravar via `PUT` um nome de 1 caractere e uma categoria inexistente que o `POST` recusava. Corrigir a exposição de `senha` exigia lembrar de dois pontos distintos.

**Recomendação**

Serializador único por entidade e schema de validação compartilhado entre criação e atualização. → RP-11

---

### [MEDIUM] 13. Validação de entrada ausente ou superficial na rota

- **Anti-pattern:** AP-14
- **Arquivo(s):** `controllers.py:146-165`, `:188-201`, `:64-96`, `:111-126`

**Descrição**

`criar_usuario` validava só presença — sem formato de e-mail, sem política de senha (aceitava um caractere) e sem checagem de duplicidade (o schema não tinha `UNIQUE`). `criar_pedido` não validava tipo nem faixa de `quantidade`. `buscar_produtos` fazia `float(preco_min)` sem tratar entrada não numérica. Nenhuma biblioteca ou camada de schema era usada.

**Impacto**

`POST /produtos {"preco": "abc"}` estourava `TypeError` na comparação `preco < 0` e virava 500; `GET /produtos/busca?preco_min=abc` idem. Usuários duplicados com o mesmo e-mail tornavam o login não determinístico.

**Recomendação**

Middleware de validação por schema aplicado antes do controller. → RP-11

---

### [MEDIUM] 14. Listagem sem paginação nem limite

- **Anti-pattern:** AP-12
- **Arquivo(s):** `models.py:7`, `:75`, `:206`, `:299`

**Descrição**

Nenhum `LIMIT`/`OFFSET` no projeto inteiro e nenhum endpoint aceitava `page` ou `per_page`. O relatório de vendas (`models.py:239-254`) varria a tabela `pedidos` cinco vezes inteiras, sem filtro.

**Impacto**

`GET /pedidos` com 500 mil pedidos carregaria a tabela inteira em memória e, somado ao N+1, dispararia milhões de queries.

**Recomendação**

`LIMIT`/`OFFSET` com default e teto; agregação do relatório feita no banco. → RP-16

---

### [LOW] 15. Magic numbers e strings literais de domínio

- **Anti-pattern:** AP-16
- **Arquivo(s):** `models.py:257-262`; `controllers.py:47-50`, `:52`, `:242`; `database.py:5`

**Descrição**

Faixas de desconto `> 10000 → 0.1`, `> 5000 → 0.05`, `> 1000 → 0.02`; limites de nome 2 e 200; lista de categorias e lista de status válidos literais dentro dos handlers; porta e caminho do banco fixos. Nenhum bloco de constantes existia.

**Impacto**

Mudar uma faixa de desconto exigia achar o número solto no meio de um model de 314 linhas, e a lista de status no controller não conversava com o default `'pendente'` do schema.

**Recomendação**

`config/constants.py` com faixas, limites e enums. → RP-12

---

### [LOW] 16. `print` como mecanismo de log

- **Anti-pattern:** AP-17
- **Arquivo(s):** `controllers.py:8`, `:11`, `:57`, `:61`, `:106`, `:161`, `:179`, `:182`, `:208-210`, `:219`, `:248`, `:250`; `app.py:56`, `:83-86` (19 ocorrências)

**Descrição**

`print()` como único mecanismo de log — sem nível, timestamp ou destino —, registrando dado pessoal em claro (`print("Login bem-sucedido: " + email)`). Agravante: `controllers.py:208-210` e `:248-250` usavam `print` **no lugar** do efeito colateral real — "ENVIANDO EMAIL", "ENVIANDO SMS", "ENVIANDO PUSH" e "Devolver estoque" eram funcionalidades inexistentes, fingidas por um log.

**Impacto**

Sem log estruturado não havia como investigar produção, e e-mails de usuários iam para o stdout capturado por Docker/CloudWatch. O cliente recebia 201 acreditando ter sido notificado, e o estoque nunca era reposto no cancelamento.

**Recomendação**

`logging` com níveis, e a notificação explicitada como serviço injetado em vez de fingida. → RP-13

---

### [LOW] 17. Código morto: imports não usados

- **Anti-pattern:** AP-19
- **Arquivo(s):** `database.py:2`; `models.py:2`; `app.py:1`

**Descrição**

`import os` em `database.py` e `import sqlite3` em `models.py` nunca eram referenciados. `request` em `app.py` só era usado pelo endpoint `/admin/query`.

**Impacto**

Sugeriam configuração por ambiente e acesso ao driver que o arquivo não praticava.

**Recomendação**

Remover. → RP-15

---

### [LOW] 18. Nomenclatura ruim

- **Anti-pattern:** AP-18
- **Arquivo(s):** `models.py:24`, `:54`, `:65`, `:89`; `controllers.py:14`, `:56`, `:64`, `:98`, `:101`

**Descrição**

`id` como parâmetro e variável local em nove pontos, sombreando o builtin `id()`. `cursor2`/`cursor3` em `models.py:187-223`. Funções homônimas em camadas diferentes (`models.criar_produto` / `controllers.criar_produto`), distinguidas só pelo prefixo do módulo.

**Impacto**

Baixo: nenhuma abreviação vazava para o contrato da API, então corrigir não é breaking change.

**Recomendação**

Nomes por camada (`ProdutoRepository`, `ProdutoService`, `ProdutoController`). → RP-15

---

## APIs deprecated

Nenhuma ocorrência encontrada.

Varredura de `datetime.utcnow()`, `datetime.utcfromtimestamp`, `Model.query.get()`, `@app.before_first_request`, `type(x) ==`, `imp`/`distutils`, `assertEquals`, `@asyncio.coroutine` e `flask.json.JSONEncoder`/`app.json_encoder` sobre os quatro arquivos: 0 matches. No manifesto, `flask 3.1.1` e `flask-cors 5.0.1` estão em major suportada — nenhuma dependência EOL.

## Cobertura da varredura

Anti-patterns verificados: 19/19. Ausente neste projeto: AP-15 (APIs deprecated).

## Resultado da Refatoração

### Estrutura antes → depois

**Antes** — 4 arquivos, 780 linhas:

```
code-smells-project/
├── app.py           88 linhas   rotas + 2 endpoints admin com SQL cru
├── controllers.py  292 linhas   validação + regra + notificação fingida + SQL no health
├── models.py       314 linhas   SQL concatenado + regra de negócio + serialização (4 domínios)
└── database.py      86 linhas   conexão global + DDL + seed com senha em texto puro
```

**Depois** — 27 módulos, 1.388 linhas (o maior arquivo tem 132):

```
code-smells-project/
├── app.py                          entry point (preserva `python app.py`)
├── .env.example                    chaves versionadas, valores fake
├── requirements.txt                + python-dotenv
└── src/
    ├── app.py                      create_app() — composition root
    ├── config/
    │   ├── settings.py             env tipada, SECRET_KEY obrigatória
    │   └── constants.py            faixas de desconto, limites, StatusPedido, TipoUsuario
    ├── domain/errors.py            DomainError, ValidacaoError, NaoEncontradoError,
    │                               CredenciaisInvalidasError, RegraDeNegocioError
    ├── infrastructure/
    │   ├── database.py             Database: sessao()/transacao()/migrar(), FK + PRAGMA
    │   └── logger.py               logging estruturado
    ├── models/
    │   ├── produto_model.py        ProdutoRepository + serializador único
    │   ├── usuario_model.py        UsuarioRepository + serializador sem credencial
    │   └── pedido_model.py         PedidoRepository — JOIN e agregação
    ├── services/
    │   ├── produto_service.py      usuario_service.py      pedido_service.py
    │   ├── relatorio_service.py    health_service.py       notification_service.py
    ├── controllers/                produto · usuario · pedido · relatorio · health
    ├── views/routes.py             rota → controller, 17 rotas
    ├── middlewares/
    │   ├── error_handler.py        handler central
    │   ├── validation.py           validar_corpo(schema)
    │   └── pagination.py           page/per_page com teto de 100
    └── schemas/                    validators.py + produto/usuario/pedido
```

Os quatro arquivos legados foram removidos (`git rm controllers.py models.py database.py`); `app.py` na raiz permanece como entry point, agora só importando `create_app()`.

### Findings resolvidos

| # | Severidade | Finding | Status | Onde foi resolvido |
|---|---|---|---|---|
| 1 | CRITICAL | SQL Injection | ✅ Resolvido | `src/models/*.py` — 100% parametrizado, inclusive a busca dinâmica e o `LIKE`. Varredura final: 0 matches |
| 2 | CRITICAL | Exposição de dado sensível | ✅ Resolvido | `senha` fora da serialização (`usuario_model.py`), `/health` enxuto, `/admin/*` removidos, erro sem `str(e)` |
| 3 | CRITICAL | Segredos hardcoded | ✅ Resolvido | `src/config/settings.py` + `.env.example`; `DEBUG=false` e `CORS_ORIGINS` restrito por default; `HOST` default `127.0.0.1` |
| 4 | CRITICAL | Autenticação quebrada | ✅ Resolvido | Hash `scrypt` via `werkzeug.security`, coluna `senha_hash`, seed hasheado, comparação fora do SQL, login com custo constante contra hash dummy (sem enumeração de contas), endpoints administrativos sem autenticação removidos |
| 5 | CRITICAL | God Module | ✅ Resolvido | 27 módulos, uma responsabilidade cada; maior arquivo 132 linhas |
| 6 | HIGH | Regra no controller/model | ✅ Resolvido | `src/services/` — nenhum `request`/`jsonify` nas camadas internas (varredura limpa) |
| 7 | HIGH | Sem injeção de dependência | ✅ Resolvido | `create_app()` constrói `Database`, repositórios e services e injeta; nenhum módulo abre a própria conexão |
| 8 | HIGH | Estado global mutável | ✅ Resolvido | `Database.sessao()`/`transacao()` abrem e fecham conexão por operação; `global` eliminado, `check_same_thread=False` removido |
| 9 | HIGH | Escrita sem transação | ✅ Resolvido | `PedidoService.criar` roda em `BEGIN/COMMIT/ROLLBACK`; baixa de estoque condicional; `FOREIGN KEY` + `PRAGMA foreign_keys = ON` |
| 10 | HIGH | Erro engolido/espalhado | ✅ Resolvido | `src/middlewares/error_handler.py`; os 19 `try/except` desapareceram; stack trace no log, resposta sem detalhe |
| 11 | MEDIUM | Query N+1 | ✅ Resolvido | `pedido_model.py` com `LEFT JOIN` + índices. Medido: 20 pedidos × 3 itens = **3 queries** (antes: 81) |
| 12 | MEDIUM | Duplicação de regra | ✅ Resolvido | `schemas/produto_schema.py` usado por POST e PUT; um serializador por entidade; `_montar()` compartilhado pelas duas listagens |
| 13 | MEDIUM | Validação ausente | ✅ Resolvido | `validar_corpo(schema)` nas rotas de escrita; tipos, faixas, mínimo de senha, `UNIQUE` em `usuarios.email` |
| 14 | MEDIUM | Sem paginação | ✅ Resolvido | `middlewares/pagination.py`, teto de 100 itens; relatório agora é uma agregação `SUM/COUNT` |
| 15 | LOW | Magic numbers | ✅ Resolvido | `config/constants.py` — `FAIXAS_DESCONTO`, limites de nome, `StatusPedido`, `CATEGORIAS_VALIDAS` |
| 16 | LOW | `print` como log | ✅ Resolvido | `infrastructure/logger.py`; as notificações fingidas viraram `NotificationService` injetado, que registra em WARNING que o gateway não está configurado |
| 17 | LOW | Código morto | ✅ Resolvido | Arquivos legados removidos junto com os imports não usados |
| 18 | LOW | Nomenclatura | ✅ Resolvido | `produto_id`/`usuario_id`/`pedido_id`; sufixo de camada (`...Repository`/`Service`/`Controller`). O parâmetro `id` permanece apenas na assinatura das rotas `/<int:id>`, para não alterar o contrato |

**Nota de escopo sobre o finding 4.** Todos os sinais que o catálogo define como AP-04 estão fechados e verificados: nenhum MD5/SHA1, nenhuma senha em texto puro, nenhuma comparação direta `senha ==`, nenhum token previsível e nenhuma enumeração de contas por tempo de resposta. O sinal de autorização previsto no catálogo — "um método `is_admin()` definido e nunca chamado" — não se aplica: o código legado não define nenhuma função de autorização (verificado por varredura de `is_admin`, `require_`, `@login`, `role` nos quatro arquivos originais: zero ocorrências).

Adicionar um sistema de autenticação com token exigiria um cabeçalho `Authorization` em toda chamada de escrita — mudança de contrato bem além das duas exceções que a regra de preservação de comportamento autoriza (remover campo de senha da resposta e remover endpoint de SQL arbitrário). Por isso não foi implementado. Ver "Recomendações além do escopo desta refatoração", ao final.

### Validação

Executada com a aplicação real em `http://127.0.0.1:5000`, comparando as **mesmas 32 chamadas** (19 endpoints, incluindo casos de erro) antes e depois, a partir de um banco recriado do zero nas duas execuções.

| Verificação | Resultado |
|---|---|
| Aplicação sobe sem erro | ✅ `python app.py` — sem traceback |
| Endpoints originais respondem | ✅ 27/32 chamadas idênticas em status e corpo (ignorando timestamp volátil e o campo aditivo `meta`); as 5 divergências são as correções de segurança declaradas |
| Casos de borda (suíte extra) | ✅ 36 casos comparados contra a versão legada restaurada do git, rodando lado a lado: 23 idênticos, 13 divergências, todas listadas e justificadas nas seções abaixo |
| Varredura final do catálogo | ✅ 0 anti-patterns CRITICAL/HIGH remanescentes |
| Transação com rollback | ✅ falha no meio do pedido não grava nada |
| N+1 eliminado | ✅ 81 queries → 3 |
| Integridade referencial | ✅ `FOREIGN KEY constraint failed` em item órfão |

**Boot da aplicação refatorada:**

```
2026-08-17 22:14:14,001 INFO loja servidor iniciado em http://127.0.0.1:5000
 * Serving Flask app 'src.app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
2026-08-17 22:14:14,522 INFO werkzeug 127.0.0.1 - - [17/Aug/2026 22:14:14] "GET /health HTTP/1.1" 200 -
```

**Comparação das 32 chamadas (status legado → status novo, forma do JSON):**

```
OK  index: status 200->200 | forma igual
OK  listar_produtos: status 200->200 | forma igual (+meta de paginação, campo novo)
OK  buscar_produtos: status 200->200 | forma igual (+meta de paginação, campo novo)
OK  buscar_produto: status 200->200 | forma igual
OK  buscar_produto_404: status 404->404 | forma igual
OK  criar_produto: status 201->201 | forma igual
OK  criar_produto_400: status 400->400 | forma igual
OK  criar_produto_cat: status 400->400 | forma igual
OK  atualizar_produto: status 200->200 | forma igual
OK  atualizar_404: status 404->404 | forma igual
OK  deletar_produto: status 200->200 | forma igual
OK  deletar_404: status 404->404 | forma igual
OK  criar_usuario: status 201->201 | forma igual
OK  criar_usuario_400: status 400->400 | forma igual
OK  buscar_usuario_404: status 404->404 | forma igual
OK  login_ok: status 200->200 | forma igual
OK  login_401: status 401->401 | forma igual
OK  login_400: status 400->400 | forma igual
OK  criar_pedido: status 201->201 | forma igual
OK  criar_pedido_400: status 400->400 | forma igual
OK  criar_pedido_estoq: status 400->400 | forma igual
OK  criar_pedido_inex: status 400->400 | forma igual
OK  listar_pedidos: status 200->200 | forma igual (+meta de paginação, campo novo)
OK  pedidos_usuario: status 200->200 | forma igual (+meta de paginação, campo novo)
OK  status_pedido: status 200->200 | forma igual
OK  status_invalido: status 400->400 | forma igual
OK  relatorio: status 200->200 | forma igual
DIFF listar_usuarios: campo "senha" removido do payload      (breaking change declarado)
DIFF buscar_usuario:  campo "senha" removido do payload      (breaking change declarado)
DIFF health:          secret_key/debug/db_path/ambiente removidos (breaking change declarado)
DIFF admin_query:     status 200->404                        (endpoint removido)
DIFF admin_reset:     status 200->404                        (endpoint removido)
```

Valores conferidos, não só a forma — o relatório de vendas devolve exatamente os mesmos números nas duas versões:

```
legado: {"desconto_aplicavel":308.99,"faturamento_bruto":6179.79,"faturamento_liquido":5870.8,
         "pedidos_aprovados":1,"pedidos_cancelados":0,"pedidos_pendentes":0,
         "ticket_medio":6179.79,"total_pedidos":1}
novo:   {"desconto_aplicavel":308.99,"faturamento_bruto":6179.79,"faturamento_liquido":5870.8,
         "pedidos_aprovados":1,"pedidos_cancelados":0,"pedidos_pendentes":0,
         "ticket_medio":6179.79,"total_pedidos":1}
```

**Provas das correções de segurança e de integridade:**

```
1) SQLi no login que derrubava a autenticação:
   POST /login {"email":"admin@loja.com' OR '1'='1", ...}
   -> {"erro":"Email ou senha inválidos","sucesso":false} [HTTP 401]

2) senha no banco:
   admin@loja.com -> scrypt:32768:8:1$i1GbgMmwgFuKuwFa$09dbb754efd...
   colunas de usuarios: ['id','nome','email','senha_hash','tipo','criado_em']

3) login legítimo preservado:
   POST /login {"email":"joao@email.com","senha":"123456"} -> [HTTP 200] "Login OK"

4) divergência POST/PUT corrigida (antes o PUT aceitava):
   PUT /produtos/1 {"categoria":"inexistente"} -> "Categoria inválida..." [HTTP 400]

5) tipo inválido não vira mais 500:
   POST /produtos {"preco":"abc"}       -> "Preço deve ser um número" [HTTP 400]
   GET  /produtos/busca?preco_min=abc   -> "Parâmetro preco_min inválido" [HTTP 400]

6) política de senha: POST /usuarios {"senha":"123"} -> [HTTP 400]
7) e-mail duplicado:  POST /usuarios {"email":"joao@email.com"} -> [HTTP 400]

8) N+1: QUERIES para 20 pedidos x 3 itens: 3  (legado seria 1 + 20 + 60 = 81)
9) rollback: pedidos 20->20 | itens 60->60 | estoque produto 10 80->80  => ROLLBACK OK
10) FK aplicada: FOREIGN KEY constraint failed
```

**Varredura final do catálogo sobre o código novo:**

```
AP-01 SQL Injection ................ 0 ocorrências
AP-02 Segredos hardcoded ........... 0 ocorrências
AP-05 Senha em serialização ........ 0 ocorrências
AP-08 Estado global mutável ........ 0 ocorrências
AP-10 except nu .................... 0 ocorrências
AP-15 APIs deprecated .............. 0 ocorrências
AP-17 print como log ............... 0 ocorrências
HTTP framework em service/model .... 0 ocorrências
SQL em controller/rota ............. 0 ocorrências
```

### Breaking changes (correções de segurança)

1. **`POST /admin/query` removido** — executava SQL arbitrário do corpo da requisição, sem autenticação.
2. **`POST /admin/reset-db` removido** — apagava as quatro tabelas, sem autenticação.
3. **`GET /usuarios` e `GET /usuarios/<id>` não devolvem mais `senha`.**
4. **`GET /health` não devolve mais `secret_key`, `debug`, `db_path` nem `ambiente`** — permanecem `status`, `database`, `counts` e `versao`.
5. **Respostas 500 não trazem mais a mensagem da exceção** — passam a devolver `{"erro": "Erro interno"}`, com o stack trace no log.

> A `SECRET_KEY` exposta continua no histórico do Git. Remover do código não basta: **o valor precisa ser rotacionado**, e o mesmo vale para as senhas do seed (`admin123`, `123456`, `senha123`), que estavam versionadas em texto puro.

### Outras mudanças de comportamento (não são de contrato)

Registradas por transparência — nenhuma altera rota, método ou forma de resposta:

- **Validação alinhada entre POST e PUT de produto.** O `PUT` passa a aplicar as regras de tamanho de nome e de categoria válida que só o `POST` tinha (finding 12). Payloads que o `POST` já recusava agora também são recusados no `PUT`.
- **Entradas com tipo inválido viram 400 em vez de 500.** `{"preco": "abc"}` estourava `TypeError`; agora recebe erro de validação.
- **Política de senha e e-mail único.** Senha passa a exigir 8 caracteres e `usuarios.email` ganhou `UNIQUE` — cadastros que antes passavam silenciosamente agora recebem 400.
- **`POST /pedidos` com `usuario_id` inexistente retorna 400** em vez de gravar um pedido órfão (exigência da `FOREIGN KEY`).
- **Listagens aceitam `page`/`per_page`** e devolvem um bloco `meta`. O default é 100 itens, que também é o teto.
- **Deletar produto com histórico** mantém o item do pedido com `produto_nome: "Desconhecido"` — o mesmo que a versão legada já exibia para produto ausente —, agora por `ON DELETE SET NULL` em vez de registro órfão.
- **Formatação do JSON.** A versão legada rodava com `DEBUG=True` e o Flask indentava a resposta; com `DEBUG=false` o JSON sai compacto. Mesmo documento, mesmas chaves.
- **Corpo ausente ou `Content-Type` errado retorna 400 em vez de 500.** No legado, `POST /pedidos`, `POST /login` e `POST /produtos` sem corpo JSON estouravam um 415 capturado pelo `except`, devolvendo HTTP 500 com o texto do erro do Werkzeug. Agora devolvem 400 com a mensagem de validação do próprio contrato.
- **`POST /pedidos` com `quantidade: 0` retorna 400.** O legado aceitava e gravava um pedido de total `0.0` com o item de quantidade zero.
- **404 e 405 respondem em JSON.** O legado devolvia a página HTML padrão do Flask para rota inexistente e método não permitido; o handler central passa a devolver `{"erro": "..."}`. **Os status continuam 404 e 405.**
- **`preco_min=0` / `preco_max=0` passam a filtrar.** O legado testava `if preco_min:` — `0` é falso em Python, então o filtro era silenciosamente ignorado e `preco_max=0` devolvia o catálogo inteiro. Agora `0` é um limite válido e `preco_max=0` devolve lista vazia, que é o resultado correto.
- **`total` de `/produtos/busca` conta todos os resultados, não a página.** Corrigido durante a validação: a primeira versão da refatoração devolvia o tamanho da página em `total` e em `meta.total`, o que divergiria do significado legado assim que a busca passasse de 100 resultados. Verificado com 140 resultados: `total: 140`, `dados` com 100 na página 1 e 40 na página 2.

### Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env      # preencha SECRET_KEY — sem ela o boot falha
python app.py
```

## Recomendações além do escopo desta refatoração

Itens que **não** são pendências desta entrega — nenhum deles corresponde a um sinal aberto do catálogo — mas que merecem entrar no próximo ciclo:

1. **Autenticação e autorização.** A API não exige credencial em nenhuma rota: `GET /usuarios` expõe nome e e-mail, `GET /relatorios/vendas` expõe faturamento, e qualquer anônimo cria, edita ou apaga produtos. Isso já era assim na versão legada — não é regressão da refatoração. A base para resolver já existe: senhas com hash, `POST /login` validando credencial de verdade e a coluna `tipo` (`cliente`/`admin`) no schema. Falta emitir um token assinado no login e exigi-lo por middleware nas rotas sensíveis. Como isso muda o contrato de toda chamada de escrita, deve ser tratado como versão nova da API, não como refatoração.
2. **Rotacionar os segredos expostos.** A `SECRET_KEY` e as senhas do seed (`admin123`, `123456`, `senha123`) continuam no histórico do Git. Removê-las do código não basta — os valores precisam ser trocados.
3. **Testes automatizados.** A validação desta refatoração foi feita comparando as duas versões rodando lado a lado. Com as camadas separadas e as dependências injetadas, os services agora são testáveis sem servidor nem banco real — vale converter essa suíte de comparação em testes versionados.
