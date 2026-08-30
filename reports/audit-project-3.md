# Relatório de Auditoria Arquitetural — task-manager-api

| | |
|---|---|
| **Projeto** | task-manager-api |
| **Stack** | Python 3.12.3 + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.0.52) |
| **Domínio** | Task Manager (tasks, usuários, categorias, relatórios de produtividade) |
| **Arquitetura original** | Camadas por pasta, sem controller/service — `models/`, `routes/`, `services/`, `utils/` existiam, mas 100% da regra vivia nos handlers HTTP |
| **Arquivos analisados** | 14 (1.158 linhas), sendo 1 seed e 3 `__init__` |
| **Endpoints** | 22 rotas |
| **Data** | 2026-08-22 |
| **Skill** | refactor-arch v1 |

## Resumo

| Severidade | Qtd. |
|---|---|
| CRITICAL | 4 |
| HIGH | 3 |
| MEDIUM | 6 |
| LOW | 4 |
| **Total** | **17** |

> **Correção pós-auditoria.** O finding 8 foi reclassificado de HIGH para MEDIUM
> durante a Fase 3, quando a verificação empírica derrubou parte da sua premissa.
> O detalhe está no próprio finding e na seção *Correções à auditoria*. Os
> totais acima já refletem a reclassificação (a Fase 2 havia reportado
> CRITICAL 4 / HIGH 4 / MEDIUM 5 / LOW 4).

---

## Findings

### [CRITICAL] 1. Sensitive Data Exposure

- **Anti-pattern:** AP-05
- **Arquivo(s):** `models/user.py:16-25` (`:21`) — consumido em `routes/user_routes.py:33`, `:85`, `:129`, `:209`

**Descrição**

`User.to_dict()` incluía o hash da senha na serialização:

```python
def to_dict(self):
    return {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'password': self.password,   # <-- hash MD5 na resposta
        ...
    }
```

Como esse método era a serialização única de usuário, quatro endpoints devolviam
o hash: `GET /users/<id>`, `POST /users` (201), `PUT /users/<id>` e `POST /login`
(dentro da chave `user`). `GET /users` escapava por montar o dicionário à mão
(`user_routes.py:15-23`), o que já provava que os dois formatos haviam divergido.

**Impacto**

Confirmado em execução: `GET /users/1` devolvia
`"password": "81dc9bdb52d04dc20036dbd8313ed055"` — o MD5 conhecido de `"1234"`.
Combinado com o finding 2 (MD5 sem salt), vazar o hash equivalia a vazar a senha.

**Recomendação**

Remover o campo da serialização da entidade. → RP-02 / RP-04. **Breaking change.**

---

### [CRITICAL] 2. Broken Authentication / Weak Password Hashing

- **Anti-pattern:** AP-04
- **Arquivo(s):** `models/user.py:27-32`, `:34-38`; `routes/user_routes.py:185-211` (`:197-202`, `:210`)

**Descrição**

Quatro defeitos com a mesma raiz:

- `set_password`/`check_password` usavam `hashlib.md5` sem salt (`models/user.py:29` e `:32`);
- o "token" emitido era `'fake-jwt-token-' + str(user.id)` (`user_routes.py:210`) — sem assinatura, sem expiração, previsível;
- nenhuma das 22 rotas verificava esse token; `User.is_admin()` (`models/user.py:34`) estava definido e **nunca era chamado** em lugar nenhum do repositório — não havia controle de acesso;
- enumeração por tempo no login: `user_routes.py:198-199` devolvia 401 assim que o e-mail não era encontrado, **antes** de `check_password` (`:201`). As mensagens já eram uniformes, mas o caminho do e-mail inexistente pulava o cálculo do hash.

**Impacto**

`DELETE /users/<id>`, `PUT /tasks/<id>` e `/reports/summary` eram executáveis por
qualquer um com acesso à rede. Um atacante forjava o token de qualquer usuário
sabendo apenas o id. As senhas do seed (`1234`, `abcd`, `pass`) caem em MD5
instantaneamente.

**Recomendação**

Hash salgado, JWT assinado com expiração, middleware de autenticação e uso real
de `is_admin()`; comparar contra hash dummy quando o usuário não existir. → RP-04.

---

### [CRITICAL] 3. Hardcoded Credentials & Insecure Configuration

- **Anti-pattern:** AP-02
- **Arquivo(s):** `app.py:11`, `:13`, `:15`, `:34`; `services/notification_service.py:7-10`

**Descrição**

- `app.py:13` — `app.config['SECRET_KEY'] = 'super-secret-key-123'`;
- `notification_service.py:9-10` — `email_user = 'taskmanager@gmail.com'` e `email_password = 'senha123'`, usados em `smtplib.login` (`:17`);
- `app.py:11` — URI do banco fixa no código;
- `app.py:34` — `app.run(debug=True, host='0.0.0.0')`;
- `app.py:15` — `CORS(app)` sem restrição de origem.

`python-dotenv` estava declarado em `requirements.txt:6` e nunca era importado —
o mecanismo de configuração externa já havia sido contratado e não usado.

**Impacto**

Os segredos ficam versionados no histórico do Git; rotacionar o valor não remove
o commit. O `debug=True` foi confirmado em execução: o boot imprimia
`Debugger is active! Debugger PIN: 757-815-489` ligado em `0.0.0.0`, e um erro
qualquer devolvia o **console interativo do Werkzeug** — execução remota de
código arbitrário na rede.

**Recomendação**

Variáveis de ambiente com `.env.example` versionado e defaults seguros; CORS
restrito. → RP-02.

---

### [CRITICAL] 4. God Module / God Method

- **Anti-pattern:** AP-03
- **Arquivo(s):** `routes/task_routes.py:1-299`; `routes/report_routes.py:1-223`; `routes/user_routes.py:1-211`

**Descrição**

Os três arquivos de rota somavam **733 das 1.158 linhas** do projeto, e cada um
acumulava 5 responsabilidades: roteamento HTTP, validação, regra de negócio,
acesso a dados e serialização.

Métodos gigantes:

| Handler | Arquivo:linhas | Tamanho |
|---|---|---|
| `summary_report` | `report_routes.py:12-101` | 90 linhas |
| `create_task` | `task_routes.py:85-154` | 70 linhas |
| `update_task` | `task_routes.py:156-223` | 68 linhas |
| `get_tasks` | `task_routes.py:11-63` | 53 linhas, 4 níveis de aninhamento |
| `create_user` | `user_routes.py:42-90` | 49 linhas |

`report_routes.py` ainda misturava dois domínios: relatórios (`:12-155`) e CRUD
completo de categorias (`:157-223`).

**Impacto**

Não havia como testar "uma task está atrasada" sem subir Flask e SQLite juntos e
emitir um request HTTP.

**Recomendação**

Controllers finos por entidade + services + repositories. → RP-03.

---

### [HIGH] 5. Business Logic in Controller (no service layer)

- **Anti-pattern:** AP-06
- **Arquivo(s):** `routes/task_routes.py:89-145`, `:273-299`; `routes/user_routes.py:54-78`, `:194-206`; `routes/report_routes.py:15-99`, `:111-153`

**Descrição**

100% da regra de negócio vivia dentro do handler HTTP: cálculo de atraso
reimplementado inline em 6 pontos (`task_routes.py:30-39`, `:71-80`, `:284-287`;
`user_routes.py:171-180`; `report_routes.py:34-43`, `:132-135`), cálculo de
`completion_rate` em 3 (`task_routes.py:296`; `report_routes.py:67`, `:151`),
política de senha e role (`user_routes.py:64-72`), parsing de tags e datas
(`task_routes.py:134-144`).

A pasta `services/` existia e continha um único módulo que nenhum arquivo
importava — a camada de serviço era nominal.

**Impacto**

A regra só era alcançável por requisição HTTP: não dava para reusá-la num job de
"notificar tasks atrasadas" — que é justamente o que
`notification_service.notify_task_overdue` prometia e nunca era chamado.

**Recomendação**

Extrair services puros, sem `request`/`jsonify`. → RP-05.

---

### [HIGH] 6. Swallowed / Scattered Error Handling

- **Anti-pattern:** AP-10
- **Arquivo(s):** `routes/task_routes.py:62-63`, `:137`, `:204`, `:236`; `routes/user_routes.py:130`, `:149`; `routes/report_routes.py:186`, `:207`, `:221`; `utils/helpers.py:46`, `:49`, `:88`

**Descrição**

12 blocos `except:` nus — capturam até `KeyboardInterrupt` e `SystemExit`. O pior
era `task_routes.py:62-63`, envolvendo o handler inteiro de `GET /tasks`:

```python
    except:
        return jsonify({'error': 'Erro interno'}), 500
```

Onde havia `except Exception as e` (`task_routes.py:151`, `:221`;
`user_routes.py:87`), o erro ia para `print()`, não para um logger, e
`task_routes.py:221` nem usava a variável `e` capturada. Não existia nenhum
`@app.errorhandler` registrado e o módulo `logging` nunca era importado
(0 ocorrências no repositório).

**Impacto**

Um bug em produção ficava invisível — sem stack trace no log e sem detalhe na
resposta. O mesmo `try/except` repetido em 9 handlers era código duplicado.

**Recomendação**

Error handler central + exceções de domínio + logging estruturado. → RP-10.

---

### [HIGH] 7. Tight Coupling / No Dependency Injection

- **Anti-pattern:** AP-07
- **Arquivo(s):** `database.py:1-3`; `app.py:3`, `:11`, `:16`; `models/task.py:1`; `models/user.py:1`; `models/category.py:1`; `routes/task_routes.py:2`; `routes/user_routes.py:2`; `routes/report_routes.py:2`

**Descrição**

Os 7 módulos importavam o singleton `db` diretamente de `database.py`; a
configuração da conexão era escrita dentro do entry point (`app.py:11-12`) em vez
de injetada. `datetime.utcnow()` era chamado **19 vezes** no meio da regra de
negócio, tornando o relógio uma dependência oculta. `NotificationService`
instanciava o próprio cliente SMTP dentro de `send_email`
(`notification_service.py:15`).

**Impacto**

Não dava para trocar SQLite por Postgres nem usar banco em memória no teste sem
editar todos os módulos. Testar borda de vencimento exigia congelar o relógio do
processo inteiro.

**Recomendação**

Application factory com config injetada; "agora" como parâmetro da regra. → RP-06.

---

### [MEDIUM] 8. Foreign Key Não Aplicada / Escrita Fora da Transação

- **Anti-pattern:** AP-09
- **Severidade:** reclassificada de HIGH para MEDIUM na Fase 3 — ver *Correções à auditoria*
- **Arquivo(s):** `models/task.py:13-14`; `routes/user_routes.py:140-146`

**Descrição**

`Task` declarava FKs para `users.id` e `categories.id` (`models/task.py:13-14`),
mas não havia nenhum `PRAGMA foreign_keys = ON` no repositório (0 ocorrências).
No SQLite, a FK declarada sem esse pragma **não é aplicada**. Verificado
empiricamente no banco original:

```
banco ORIGINAL, conexão padrão: foreign_keys=0
  -> INSERT em tasks com category_id=99999 ACEITO (FK não aplicada)
```

Além disso, `DELETE /users/<id>` apagava as tasks em laço
(`user_routes.py:141-142`) **fora** do `try` que protegia o commit (`:144-151`);
uma falha nesse laço deixaria a sessão suja sem rollback.

**Impacto**

Qualquer caminho de escrita que não passe pela validação da rota (script de
manutenção, migração, SQL direto) pode gravar uma referência inválida sem que o
banco recuse. É defesa em profundidade ausente, não um exploit alcançável pela
API — a validação em `create_task` já barra id inexistente com 404.

**Recomendação**

Habilitar `PRAGMA foreign_keys` na abertura da conexão e mover toda escrita
multi-passo para dentro de uma transação única. → RP-09.

---

### [MEDIUM] 9. N+1 Query

- **Anti-pattern:** AP-11
- **Arquivo(s):** `routes/task_routes.py:41-57`; `routes/user_routes.py:22`; `routes/report_routes.py:53-68`, `:159-164`

**Descrição**

Query dentro de laço em 4 endpoints, todos com o relacionamento do ORM **já
declarado e ignorado**:

- `GET /tasks` — para cada task, `User.query.get` (`task_routes.py:42`) e `Category.query.get` (`:51`), embora `Task.user` e `Task.category` existissem (`models/task.py:20-21`);
- `GET /users` — `len(u.tasks)` (`user_routes.py:22`) dispara lazy load por usuário;
- `GET /reports/summary` — `Task.query.all()` (`:30`) carrega a tabela inteira só para contar atrasadas, e faz um `filter_by` por usuário no laço (`:56`);
- `GET /categories` — um `COUNT` por categoria (`report_routes.py:163`).

**Impacto**

Medido com contador de `SELECT` no engine, sobre 308 tasks / 62 usuários /
23 categorias:

| Endpoint | Queries |
|---|---|
| `GET /tasks` | **607** (= 1 + 2N) |
| `GET /users` | 64 |
| `GET /reports/summary` | 79 |
| `GET /categories` | 24 |
| `GET /tasks/stats` | 6 |

**Recomendação**

`joinedload` nos relacionamentos e agregação com `COUNT`/`GROUP BY`. → RP-08.

---

### [MEDIUM] 10. Duplicated Business Rules and Validation

- **Anti-pattern:** AP-13
- **Arquivo(s):** `task_routes.py:110` e `:177`; `task_routes.py:113` e `:182`; `user_routes.py:71` e `:120`; `user_routes.py:61` e `:106`; `models/task.py:38-60`; `utils/helpers.py:57-108`

**Descrição**

A mesma regra reescrita em pontos diferentes:

- lista de status válidos literal em 2 handlers + no model (`models/task.py:39`) + em helpers (`:75`) + na constante `VALID_STATUSES` (`:110`) = **5 cópias**;
- faixa de prioridade 1-5 em `task_routes.py:113` e `:182`;
- roles válidos em `user_routes.py:71` e `:120`;
- regex de e-mail idêntico em `user_routes.py:61`, `:106` e `helpers.validate_email` (`utils/helpers.py:21`) = 3 cópias;
- regra de atraso reimplementada 6 vezes, enquanto `Task.is_overdue()` (`models/task.py:50-60`) fazia exatamente isso e nunca era chamado; idem `validate_status` (`:38`) e `validate_priority` (`:45`).

**Prova de divergência — as cópias já haviam se separado:**

- `POST /tasks` exigia título presente (`:93`) e validava tamanho (`:96`); `PUT /tasks/<id>` validava o tamanho (`:167`) mas aceitava `"title": null`, estourando `TypeError` em `len()` → 500;
- `GET /tasks` devolvia `overdue`, `user_name` e `category_name`; `GET /tasks/search` devolvia `to_dict()` puro, sem nenhum dos três (`:269`) — **dois formatos para a mesma entidade**;
- `GET /users` omitia `password` e incluía `task_count`; `GET /users/<id>` usava `to_dict()`, que incluía `password` e não tinha `task_count`.

**Impacto**

Corrigir uma regra exigia achar todas as cópias; a evidência mostra que isso já
havia falhado 3 vezes.

**Recomendação**

Regra única no service + constantes centralizadas + um serializador por entidade. → RP-11.

---

### [MEDIUM] 11. Missing / Superficial Input Validation

- **Anti-pattern:** AP-14
- **Arquivo(s):** `routes/task_routes.py:113`, `:182`, `:261`, `:264`; `routes/user_routes.py:64`, `:103`, `:115`, `:125`; `routes/report_routes.py:197-202`

**Descrição**

- `marshmallow 3.20.1` estava em `requirements.txt:4` e nunca era importado — nenhum schema, nenhum middleware de validação;
- política de senha mínima de **4** caracteres (`user_routes.py:64` e `:115`), com `MIN_PASSWORD_LENGTH = 4` definido e ignorado em `utils/helpers.py:114`;
- conversão sem guarda: `int(priority)` e `int(user_id)` em `task_routes.py:261` e `:264`;
- comparação sem checar tipo: `data['priority'] < 1` (`:182`); `len(data['title'])` (`:167`);
- `PUT /categories` nem verificava se o corpo era nulo antes de `'name' in data` (`report_routes.py:196-197`).

**Impacto**

Confirmado em execução — três caminhos devolviam **500** com o console do
Werkzeug em vez de 400:

```
GET /tasks/search?priority=alta   -> 500  ValueError: invalid literal for int()
PUT /tasks/1 {"priority":"alta"}  -> 500
PUT /tasks/1 {"title":null}       -> 500
```

**Recomendação**

Schemas marshmallow em middleware de validação; mínimo de senha para 8+. → RP-11.

---

### [MEDIUM] 12. No Pagination or Limit on Listings

- **Anti-pattern:** AP-12
- **Arquivo(s):** `routes/task_routes.py:14`, `:266`, `:281`; `routes/user_routes.py:12`, `:35`, `:159`; `routes/report_routes.py:30`, `:53`, `:109`, `:159`

**Descrição**

12 chamadas `.all()` sem `LIMIT`/`OFFSET` e nenhuma ocorrência de `paginate()`,
`page` ou `limit` no repositório. Pior caso: `report_routes.py:30` e
`task_routes.py:281` carregavam todas as tasks em memória apenas para contar as
atrasadas em laço Python.

**Impacto**

A resposta cresce sem teto junto com a tabela. `GET /users/<id>` ainda embutia
todas as tasks do usuário no mesmo payload.

**Recomendação**

Parâmetros `page`/`per_page` com default e teto; filtros de atraso no `WHERE`. → RP-16.

---

### [MEDIUM] 13. Deprecated API Usage

- **Anti-pattern:** AP-15
- **Arquivo(s):** ver tabela na seção *APIs deprecated*

**Descrição**

34 ocorrências em 3 famílias: `datetime.utcnow()` (19), `Model.query.get()` (12)
e `type(x) == list` (3).

**Impacto**

Confirmado em execução: `python seed.py` no ambiente (Python 3.12.3) emitia
`DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for
removal in a future version`. `Model.query` será removido na próxima major do
SQLAlchemy — o upgrade quebraria 12 chamadas de uma vez.

**Recomendação**

`datetime.now(timezone.utc)`, `db.session.get(Model, id)`, `isinstance(x, list)`. → RP-14.

---

### [LOW] 14. Magic Numbers and Domain String Literals

- **Anti-pattern:** AP-16
- **Arquivo(s):** `routes/task_routes.py:96`, `:99`, `:113`, `:169`, `:182`; `routes/report_routes.py:45`, `:129`; `routes/user_routes.py:64`, `:115`; `utils/helpers.py:110-116`

**Descrição**

Limites de domínio como literais espalhados: tamanho de título 3/200, faixa de
prioridade 1-5, mínimo de senha 4, `timedelta(days=7)` para "atividade recente"
(`report_routes.py:45`), e `if t.priority <= 2` codificando "alta prioridade" sem
nome (`report_routes.py:129`).

**Agravante:** `utils/helpers.py:110-116` já definia `VALID_STATUSES`,
`VALID_ROLES`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`,
`DEFAULT_PRIORITY` e `DEFAULT_COLOR` — e **nenhuma das 7** era importada por
arquivo nenhum.

**Recomendação**

Centralizar em `config/constants` e importar. → RP-12.

---

### [LOW] 15. `print()` as Logging Mechanism

- **Anti-pattern:** AP-17
- **Arquivo(s):** `routes/task_routes.py:149`, `:153`, `:219`, `:234`; `routes/user_routes.py:83`, `:89`, `:147`; `services/notification_service.py:21`, `:24`; `utils/helpers.py:39`, `:41`

**Descrição**

11 `print()` como único mecanismo de log — sem nível, sem timestamp
configurável, sem destino. Inclui log de erro (`task_routes.py:153`,
`user_routes.py:89`) e de dado pessoal (`user_routes.py:83`).
`utils/helpers.py:36-41` define `log_action()` fingindo ser um logger, nunca
chamada. `notification_service.py:21` imprime "Email enviado para {to}" — mas o
módulo inteiro nunca é acionado.

**Recomendação**

`logging` com níveis, configurado no composition root. → RP-13.

---

### [LOW] 16. Dead Code and Dead Layers

- **Anti-pattern:** AP-19
- **Arquivo(s):** `services/notification_service.py:1-48`; `utils/helpers.py:9-41`, `:52-116`; `models/task.py:38-60`; `models/user.py:34-38`; `app.py:7`; `routes/task_routes.py:7`; `routes/user_routes.py:6`; `routes/report_routes.py:8`

**Descrição**

- **Camada morta** — `services/notification_service.py` tinha **0 importadores** em todo o repositório. A classe, seus 3 métodos e a integração SMTP nunca eram acionados;
- `utils/helpers.py` tinha 1 importador (`report_routes.py:7` importa `format_date` e `calculate_percentage`) e **nenhuma das duas era chamada** — apareciam só na linha do import. As outras 7 funções e as 7 constantes não eram importadas por ninguém. `process_task_data` (`:57-108`) era uma reimplementação completa da validação de task: 51 linhas mortas;
- métodos de model mortos: `Task.validate_status`, `Task.validate_priority`, `Task.is_overdue`, `User.is_admin`;
- imports não usados: `app.py:7` (`os, sys, json`), `task_routes.py:7` (`json, os, sys, time` — nenhum usado), `user_routes.py:6` (`hashlib, json`), `report_routes.py:8` (`json`), `models/task.py:3` (`json`), `helpers.py:3-7` (`os, json, sys, math, hashlib`);
- dependências declaradas e nunca importadas: `marshmallow`, `requests`, `python-dotenv`.

**Impacto**

A estrutura de pastas anunciava uma arquitetura que o código não praticava.

**Recomendação**

Remover ou ativar. → RP-15.

---

### [LOW] 17. Poor Naming

- **Anti-pattern:** AP-18
- **Arquivo(s):** `routes/report_routes.py:24-28`, `:55-68`, `:161-164`; `routes/task_routes.py:16-59`, `:268-269`, `:283-287`; `routes/user_routes.py:14-24`, `:161-181`; `models/category.py:14`

**Descrição**

Variáveis de uma letra em laços longos (`t`, `u`, `c`, `p`, `n`, `d`). Caso pior:
`report_routes.py:24-28` usa `p1..p5` para contagens que a resposta renomeia para
`critical/high/medium/low/minimal` — o nome no código não tem relação com o
significado. `get_tasks` usa `t` ao longo de 44 linhas.

**Impacto**

Nenhuma abreviação vazava para o payload público, então a correção **não** é
breaking change.

**Recomendação**

Nomes de domínio. → RP-15.

---

## APIs deprecated

| Família | Ocorrências | Substituto |
|---|---|---|
| `datetime.utcnow()` | 19 — `models/task.py:52`; `task_routes.py:31`, `:72`, `:215`, `:285`; `report_routes.py:35`, `:42`, `:45`, `:71`, `:133`; `user_routes.py:172`; `helpers.py:38`; `notification_service.py:35`; `seed.py` (5) | `datetime.now(timezone.utc)` |
| `Model.query.get()` | 12 — `task_routes.py:67`, `:117`, `:122`, `:158`, `:188`, `:195`, `:227`; `user_routes.py:29`, `:94`, `:136`, `:155`; `report_routes.py:105`, `:192`, `:213` | `db.session.get(Model, id)` |
| `type(x) == list` | 3 — `task_routes.py:141`, `:210`; `helpers.py:103` | `isinstance(x, list)` |

Confirmado em execução: `DeprecationWarning` emitido pelo Python 3.12.3 ao rodar
`seed.py` no código original.

## Cobertura da varredura

Anti-patterns verificados: **19/19**.

Ausentes neste projeto (confirmado por leitura, não por omissão):

- **AP-01 SQL Injection** — todo acesso a dados passa pelo ORM com parâmetros ligados. `task_routes.py:252-254` usa f-string dentro de `.like()`, mas o valor vira bind parameter; o único efeito é que `%` e `_` do usuário não são escapados (LIKE pattern injection, sem risco de leitura de dados).
- **AP-08 Estado global mutável** — nenhuma variável mutável em escopo de módulo e nenhum `global`. `NotificationService.notifications` (`notification_service.py:6`) é estado de instância e a classe nunca é instanciada.

---

## Correções à auditoria

Registro das afirmações da Fase 2 que a verificação empírica da Fase 3 derrubou.

### Finding 8 — a alegação de registros órfãos estava errada

A Fase 2 afirmou que `DELETE /categories/<id>` deixava as tasks com
`category_id` apontando para uma linha inexistente, e classificou o achado como
HIGH com base nisso. **Isso não acontecia.**

O teste lado a lado mostrou que o código original já anulava o campo:

```
ANTES (app original), tasks da categoria 1:
  [(1, 1, 'Backend'), (5, 1, 'Backend'), (6, 1, 'Backend'), (8, 1, 'Backend')]
  DELETE /categories/1 -> 200
ANTES, as mesmas tasks depois do delete:
  []                       <- nenhuma task ficou com category_id = 1

Consulta direta ao banco original:
  tasks (id, category_id): [(1, None), (2, 2), (4, 4), (5, None), (6, None), ...]
  tasks com category_id órfão: 0
```

O motivo é o comportamento padrão do SQLAlchemy para um relacionamento
um-para-muitos: ao deletar o pai, o ORM anula a chave estrangeira dos filhos que
conhece. A ausência de `ondelete`/`cascade` no model não implicava órfãos, como
a auditoria deduziu — a dedução foi feita a partir do grep, sem execução.

**O que permanece verdadeiro no finding 8:** o `PRAGMA foreign_keys` realmente
não existia e a FK realmente não era aplicada pelo SQLite (medido: `foreign_keys=0`,
`INSERT` com `category_id=99999` aceito). E o laço de exclusão de tasks em
`user_routes.py:141-142` realmente ficava fora do `try`.

**Consequência:** o finding foi reclassificado de **HIGH para MEDIUM**, porque o
impacto real é defesa em profundidade ausente, não corrupção de dados alcançável
pela API. O resumo no topo deste relatório já reflete a reclassificação.

---

## Resultado da Refatoração

### Estrutura antes → depois

**Antes** — 14 arquivos, 1.158 linhas, 733 delas em `routes/`:

```
app.py                      34    entry point + config + 2 rotas + create_all
database.py                  3    singleton db
seed.py                     99
models/
├── task.py                 60    entidade + regra + serialização
├── user.py                 38    entidade + hashing MD5 + serialização com senha
└── category.py             21
routes/
├── task_routes.py         299    7 rotas: HTTP + validação + regra + SQL + serialização
├── user_routes.py         211    7 rotas: idem + autenticação
└── report_routes.py       223    6 rotas: relatórios + CRUD de categorias
services/
└── notification_service.py 48    0 importadores — camada morta
utils/
└── helpers.py             116    2 de 9 símbolos importados, 0 chamados
```

**Depois** — 35 arquivos com conteúdo, 2.388 linhas, maior arquivo com 188:

```
app.py                        16   entry point: create_app() + app.run()
seed.py                      110
.env.example                        todas as variáveis suportadas
.gitignore                          .env, instance/, *.db
src/
├── app.py                    89   composition root: monta e injeta
├── config/
│   ├── settings.py           76   configuração lida do ambiente (sem flag de auth)
│   └── constants.py          77   Status, Role, Priority, limites, thresholds
├── domain/
│   └── errors.py             67   exceções de domínio → status HTTP
├── infrastructure/
│   ├── database.py           24   instância do ORM + PRAGMA foreign_keys
│   ├── clock.py              23   fonte de tempo injetável
│   ├── logger.py             26   logging estruturado
│   └── security.py           87   hash scrypt + JWT HS256
├── models/
│   ├── task_model.py         87   entidade + is_overdue + 4 serializadores
│   ├── user_model.py         48   entidade + set/check_password + is_admin
│   └── category_model.py     23
├── repositories/
│   ├── task_repository.py   188   eager loading + agregações GROUP BY
│   ├── user_repository.py    33
│   └── category_repository.py 30
├── services/
│   ├── task_service.py      153   regra de negócio, sem HTTP
│   ├── user_service.py      120   inclui autenticação sem enumeração
│   ├── category_service.py   61
│   ├── report_service.py    118
│   └── notification_service.py 61  agora com 4 importadores
├── controllers/
│   ├── task_controller.py    68   8 métodos
│   ├── user_controller.py    38   8 métodos
│   ├── category_controller.py 25
│   ├── report_controller.py  13
│   └── health_controller.py  17
├── views/
│   └── routes.py            178   22 rotas → controller + PUBLIC_ROUTES declaradas
├── schemas/
│   ├── task_schema.py       127   marshmallow, compartilhado POST/PUT
│   ├── user_schema.py        97
│   └── category_schema.py    36
└── middlewares/
    ├── error_handler.py      30   3 handlers centrais
    ├── validation.py         66
    ├── pagination.py         45
    └── auth.py              126   require_auth / require_admin / require_self_or_admin
                                   / require_admin_for_role — todos incondicionais
```

> Os números desta árvore foram remedidos com `wc -l` na segunda execução da
> skill. A versão anterior do relatório trazia 2.171 linhas e 177 como maior
> arquivo, valores que já não batiam com o código entregue (eram 2.337 e 188
> antes das mudanças desta rodada) — a árvore havia sido escrita a partir de um
> estado intermediário e não foi remedida depois das correções pós-refatoração.

### Findings resolvidos

| # | Sev. | Finding | Status | Onde foi resolvido |
|---|---|---|---|---|
| 1 | CRITICAL | Sensitive Data Exposure | ✅ Resolvido | `src/models/user_model.py:33-44` — `to_dict()` sem `password`; verificado nos 4 endpoints |
| 2 | CRITICAL | Broken Authentication | ✅ Resolvido | `src/infrastructure/security.py` — scrypt (Werkzeug) + JWT HS256 assinado com `exp`; `src/services/user_service.py` — hash dummy contra enumeração; `src/middlewares/auth.py` — `require_auth`, `require_admin`, `require_self_or_admin` e `require_admin_for_role`, usando `is_admin()`, **sem flag e sempre ativos**; `src/views/routes.py` — 18 das 22 rotas exigem token, 4 públicas declaradas em `PUBLIC_ROUTES`. Escalada de privilégio fechada. Enforcement verificado por requisição: `DELETE /users/3` sem token = `401` (ver *Segunda execução da skill*) |
| 3 | CRITICAL | Hardcoded Credentials | ✅ Resolvido | `src/config/settings.py` + `.env.example`; `DEBUG=false`, host `127.0.0.1`, CORS restrito; `SECRET_KEY` obrigatória em produção |
| 4 | CRITICAL | God Module / God Method | ✅ Resolvido | 733 linhas de `routes/` viraram controllers (13-65 linhas), services, repositories e schemas; maior arquivo do projeto: 177 linhas |
| 5 | HIGH | Business Logic in Controller | ✅ Resolvido | `src/services/` — 5 services sem `request`/`jsonify`; `is_overdue` e `completion_rate` com implementação única |
| 6 | HIGH | Swallowed Error Handling | ✅ Resolvido | `src/middlewares/error_handler.py` — 3 handlers centrais; **0 `except:` nus** no código novo; logging com `exc_info` |
| 7 | HIGH | Tight Coupling / No DI | ✅ Resolvido | `src/app.py` — `create_app(settings, clock, notifier)`; repositories recebem a sessão; relógio isolado em `src/infrastructure/clock.py` |
| 8 | MEDIUM | FK Não Aplicada / Escrita Fora da Transação | ✅ Resolvido | `src/infrastructure/database.py:12-24` — `PRAGMA foreign_keys=ON` por conexão (medido: `0 → 1`); escritas em `begin_nested()` + `commit` |
| 9 | MEDIUM | N+1 Query | ✅ Resolvido | `src/repositories/task_repository.py` — `joinedload` e `GROUP BY`; medição abaixo |
| 10 | MEDIUM | Duplicated Rules | ✅ Resolvido | `src/config/constants.py` (fonte única), `src/schemas/` (POST e PUT compartilham as regras), `Task.is_overdue()` agora é chamado pelos 4 pontos |
| 11 | MEDIUM | Missing Input Validation | ✅ Resolvido | `src/schemas/` com marshmallow (a dependência declarada e não usada); os 3 caminhos que davam 500 agora dão 400 |
| 12 | MEDIUM | No Pagination | ⚠️ Parcial | `src/middlewares/pagination.py` — `page`/`per_page` com teto de 100 e header `X-Total-Count` em todas as listagens (exposto no CORS). **Opt-in**: sem os parâmetros, a listagem completa é mantida para não quebrar o contrato |
| 13 | MEDIUM | Deprecated APIs | ✅ Resolvido | 0 ocorrências de `utcnow()`, `Model.query.get()` e `type(x) ==` no código novo |
| 14 | LOW | Magic Numbers | ✅ Resolvido | `src/config/constants.py` — as 7 constantes órfãs agora são a fonte única e são importadas; `Status`, `Role` e `Priority` são `Enum`, e o mapa 1..5 → `critical/high/medium/low/minimal` deriva de `Priority.label` em vez de literais em `report_service.py` |
| 15 | LOW | `print()` as Logging | ✅ Resolvido | `src/infrastructure/logger.py`; `print` só em `seed.py`, que é script CLI |
| 16 | LOW | Dead Code / Dead Layers | ✅ Resolvido | `notification_service` foi **ligado ao fluxo** (0 → 4 importadores) e dispara em `create_task`; `helpers.py` removido, suas partes vivas absorvidas por `constants.py` e `schemas/`; imports mortos eliminados (pyflakes limpo); `requests` removido do `requirements.txt` — `marshmallow` e `python-dotenv` passaram a ser usados de fato |
| 17 | LOW | Poor Naming | ✅ Resolvido | `task`, `user`, `category`, `priority_critical` no lugar de `t`, `u`, `c`, `p1..p5` |

#### Correções aplicadas na revisão pós-refatoração

Uma verificação exaustiva posterior (121 comparações contra a aplicação original
rodando em paralelo) encontrou uma regressão e algumas pendências, todas
corrigidas. Registro do que mudou:

**1. Regressão em `PUT /categories/<id>` com corpo vazio** — corpo `{}` devolvia
200 (atualização sem efeito) no código original e passou a devolver 400 na
refatoração. Causa: o `update_category` original
(`routes/report_routes.py:190-203`) **não** tinha a guarda `if not data` que o
`create_category` (`:170-172`) tinha, e o middleware de validação uniformizou por
cima dessa assimetria. Corrigido com o parâmetro `reject_empty=False` em
`validate_body`, aplicado só nessa rota. Verificado: 200 nos dois lados, mesmo corpo.

**2. Escalada de privilégio em `PUT /users/<id>` e `POST /users`** — apontada na
análise manual e não resolvida na primeira passagem: a validação conferia se o
valor de `role` era válido, nunca *quem* podia defini-lo. Qualquer chamador
promovia a si mesmo a `admin` e editava o registro de qualquer outro usuário.
Corrigido com dois novos controles em `src/middlewares/auth.py` — na época sujeitos
ao mesmo `AUTH_REQUIRED` do restante, portanto igualmente inertes nos defaults;
hoje incondicionais (ver *Segunda execução da skill*):

- `require_self_or_admin` — alterar um usuário exige ser o próprio dono ou admin;
- `require_admin_for_role` — definir ou alterar `role` exige admin; no registro
  (`POST /users`) o papel padrão `user` segue liberado, para não fechar a criação
  de conta comum.

Comportamento medido na época com `AUTH_REQUIRED=true` — hoje é o comportamento
padrão, sem flag nenhuma:

```
maria promove a SI MESMA a admin                     403
maria edita OUTRO usuario (PUT /users/1)             403
maria edita o PROPRIO nome (permitido)               200
anonimo registra-se como admin (POST /users)         401
anonimo registra-se como user (deve seguir aberto)   201
admin promove maria a admin (permitido)              200
admin edita outro usuario (permitido)                200
admin cria usuario admin (permitido)                 201
```

**3. `X-Total-Count` nas listagens** — a paginação não informava o total, então o
cliente não tinha como saber quantas páginas existiam. O header vai em
`/tasks`, `/users`, `/categories`, `/tasks/search` e `/users/<id>/tasks`, respeita
os filtros da busca e é declarado em `expose_headers` do CORS (sem isso o
JavaScript no navegador não consegue lê-lo). Fica em header, e não no corpo,
justamente para a resposta seguir sendo o array puro do contrato original. O
`COUNT` extra só é emitido quando o cliente realmente pagina — sem `page`/`per_page`
o total é o tamanho da lista já carregada, e a contagem de queries não muda.

**4. `Priority` como `Enum`** — o mapa `1..5 → critical/high/medium/low/minimal`
continuava como literais em `report_service.py`. Agora `Priority` é um `Enum` em
`src/config/constants.py`, `MIN/MAX/DEFAULT_PRIORITY` e
`HIGH_PRIORITY_THRESHOLD` derivam dele, e o relatório monta as chaves a partir de
`Priority.label`. As chaves e os valores da resposta seguem idênticos.

**5. `requests` removido do `requirements.txt`** — a dependência continuava
declarada e sem nenhum import. A tabela de findings marcava o finding 16 como
totalmente resolvido citando as três dependências mortas; `marshmallow` e
`python-dotenv` passaram a ser usados de fato, mas `requests` havia ficado para
trás. Corrigido.

**Revalidação após as correções:** 68/68 casos de escrita/erro idênticos (antes
67/68) e 46/53 de leitura, sendo os 7 restantes o corpo JSON dos erros do próprio
framework (404 de rota inexistente e 405), com status idêntico — a mudança já
registrada em *Breaking changes*.

---

#### Finding 2 — resolvido na segunda execução da skill

A primeira execução construiu a autenticação inteira — scrypt salgado, JWT HS256
assinado com expiração, middleware que valida assinatura e papel — e a deixou
**desligada por default**, atrás de `AUTH_REQUIRED=false`. O raciocínio na época
foi que exigir token quebraria as 22 rotas, indo além das duas breaking changes
aprovadas.

**Esse raciocínio estava errado, e o finding permaneceu aberto.** Com os defaults
versionados — que são o que qualquer um obtém ao clonar o repositório e rodar
`python app.py` — todo guard era inerte:

```python
if settings.AUTH_REQUIRED and not payload:   # AUTH_REQUIRED=false -> nunca levanta
    raise UnauthorizedError('Autenticação obrigatória')
```

Medido na aplicação rodando, antes da correção:

```
usuarios antes: ['João Silva', 'Maria Santos', 'Pedro Oliveira']

$ curl -i -X DELETE http://127.0.0.1:5000/users/3      # sem header Authorization
HTTP/1.1 200 OK
{"message":"Usuário deletado com sucesso"}

usuarios depois: ['João Silva', 'Maria Santos']
```

O impacto descrito neste próprio finding — *"`DELETE /users/<id>`, `PUT /tasks/<id>`
e `/reports/summary` eram executáveis por qualquer um com acesso à rede"* —
continuava valendo palavra por palavra depois da refatoração. O que a refatoração
entregou foi um `@require_admin` decorativo na rota, o que é **pior** do que não
ter feito nada: a revisão seguinte lê o decorator e presume proteção.

**Correção.** A flag foi removida do projeto — não desligada, removida. Os guards
valem sempre; o ambiente configura apenas `SECRET_KEY` e `TOKEN_TTL_SECONDS`, ou
seja, *qual* chave assina e por *quanto tempo* o token vale, nunca *se* a
verificação acontece. A regra de preservação de comportamento da skill e o
playbook (RP-04) foram corrigidos junto, para tratar "exigir autenticação" como
breaking change de segurança de mesmo peso que a remoção do campo `password` —
ver *Segunda execução da skill*, abaixo.

Comportamento verificado depois da correção, nos defaults versionados:

```
--- autenticação ---
GET /tasks           sem token                       401
GET /tasks           token de user                   200
GET /tasks           token ADULTERADO                401
GET /tasks           esquema errado (Basic)          401
--- autorização: DELETE /users ---
DELETE /users/3      sem token                       401
DELETE /users/3      token de user comum             403
DELETE /users/3      token de ADMIN                  200
--- autorização: escalada de privilégio ---
PUT /users/2  maria promove a SI MESMA a admin       403
PUT /users/1  maria edita OUTRO usuario              403
PUT /users/2  maria edita o PROPRIO nome             200
POST /users   anonimo registra-se como ADMIN         401
POST /users   anonimo registra-se como user (aberto) 201
PUT /users/2  admin promove maria a admin            200
--- escritas de dominio com token valido ---
POST /tasks         token de user                    201
POST /categories    token de user                    201
GET /reports/summary token de user                   200
```

#### Justificativa do finding 12 (MEDIUM parcial)

A paginação existe e tem teto (`MAX_PER_PAGE=100`), mas é opt-in: sem `page` ou
`per_page` na query string, a listagem completa é devolvida, como antes. Um
default que truncasse em 20 mudaria silenciosamente a resposta de todos os
clientes existentes. O anti-pattern está mitigado, não eliminado: o caminho sem
parâmetros continua sem teto.

### Validação

Todas as verificações abaixo foram executadas. A app original foi restaurada do
git em um diretório separado e mantida no ar na porta 5001, para comparar as duas
implementações lado a lado sobre bancos recém-seedados idênticos.

| Verificação | Resultado |
|---|---|
| Aplicação sobe sem erro | ✅ `python app.py` — sem traceback, `Debug mode: off`, ligada em `127.0.0.1` |
| `python seed.py` | ✅ 3 usuários, 4 categorias, 10 tasks, **0 `DeprecationWarning`** |
| Rotas registradas | ✅ 22 regras — exatamente as 22 originais |
| Endpoints de leitura (status + valores) | ✅ **22/22** idênticos |
| Escritas e caminhos de erro (status + valores) | ✅ **36/36** idênticos |
| Revalidação exaustiva pós-correções | ✅ **68/68** escrita/erro; **46/53** leitura (7 = corpo JSON de erro do framework, status idêntico) |
| Autenticação exigida nos defaults versionados | ✅ 18/22 rotas respondem `401` sem token; as 4 públicas (`GET /`, `GET /health`, `POST /login`, `POST /users`) respondem normalmente |
| Autorização | ✅ 17/17 cenários de autenticação e escalada de privilégio com o resultado esperado |
| Contrato preservado sob token válido | ✅ **26/26** casos idênticos em status e forma de resposta contra a versão anterior rodando em paralelo na porta 5001 |
| `X-Total-Count` | ✅ presente e correto nas 5 listagens, respeitando filtros |
| Probe de 36 chamadas vs linha de base | ✅ 33/36 idênticas; 3 divergências = remoção de `password` (breaking change aprovado) |
| Varredura final do catálogo | ✅ 0 anti-patterns CRITICAL/HIGH remanescentes |
| Imports mortos (pyflakes) | ✅ limpo (1 aviso: `import src.models` intencional, com `# noqa: F401`) |

**Boot da aplicação refatorada:**

```
2026-08-22 19:42:32,566 INFO     taskmanager aplicação montada env=development debug=False
 * Serving Flask app 'src.app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```

Comparar com o boot original, que expunha o debugger na rede:

```
 * Debug mode: on
 * Running on all addresses (0.0.0.0)
 * Debugger is active!
 * Debugger PIN: 757-815-489
```

**Diff completo do probe (linha de base → refatorado):**

```
16c16
< GET    /users/1     -> 200 | {active,created_at,email,id,name,password,role,tasks}
---
> GET    /users/1     -> 200 | {active,created_at,email,id,name,role,tasks}
19c19
< POST   /users       -> 201 | {active,created_at,email,id,name,password,role}
---
> POST   /users       -> 201 | {active,created_at,email,id,name,role}
22c22
< PUT    /users/2     -> 200 | {active,created_at,email,id,name,password,role}
---
> PUT    /users/2     -> 200 | {active,created_at,email,id,name,role}
```

Nenhuma outra linha diverge: os 22 endpoints respondem com o mesmo status e a
mesma forma, e a comparação campo a campo (ignorando timestamps voláteis)
confirmou os mesmos valores.

**Correção de robustez — caminhos que devolviam 500 agora devolvem 400:**

```
GET /tasks/search?priority=alta      antes 500 -> depois 400
GET /tasks/search?user_id=xyz        antes 500 -> depois 400
PUT /tasks/1 {"priority":"alta"}     antes 500 -> depois 400
PUT /tasks/1 {"title":null}          antes 500 -> depois 400
PUT /tasks/1 {"title":"titulo ok"}   antes 200 -> depois 200   (controle)
```

**Redução de queries (medida com contador no engine SQLAlchemy):**

Seed pequeno — 10 tasks, 3 usuários, 4 categorias:

| Endpoint | Antes | Depois |
|---|---|---|
| `GET /tasks` | 8 | **1** |
| `GET /users` | 4 | **2** |
| `GET /categories` | 4 | **2** |
| `GET /reports/summary` | 19 | **10** |
| `GET /tasks/stats` | 6 | **3** |
| `GET /reports/user/1` | 2 | 2 |

Com volume — 308 tasks, 62 usuários, 23 categorias:

| Endpoint | Antes | Depois |
|---|---|---|
| `GET /tasks` | **607** | **1** |
| `GET /users` | 64 | **2** |
| `GET /categories` | 24 | **2** |
| `GET /reports/summary` | 79 | **10** |
| `GET /tasks/stats` | 6 | **3** |

O ponto não é o fator de redução, é a curva: as contagens do código refatorado
são **idênticas nos dois cenários** — não crescem com o volume. As do original
crescem linearmente (`GET /tasks` = 1 + 2N, exatamente como projetado no finding 9).

**Aplicação da chave estrangeira:**

```
banco ORIGINAL,  conexão padrão:  foreign_keys=0 -> INSERT com category_id=99999 ACEITO
banco REFATORADO, PRAGMA ligado:  foreign_keys=1 -> INSERT REJEITADO (FOREIGN KEY constraint failed)
PRAGMA foreign_keys na sessão da app refatorada: 1
```

**Camada de notificação, antes morta, agora acionada:**

```
INFO taskmanager task criada id=11 title=Task atribuida ao Joao
INFO taskmanager notificação suprimida (SMTP_ENABLED=false) destino=joao@email.com assunto=Nova task atribuída: ...
```

**Varredura final do catálogo sobre o código novo:**

| Sinal | Resultado |
|---|---|
| SQL por concatenação | limpo |
| Segredos hardcoded | limpo (restam só as senhas de fixture do `seed.py` e comentários que citam o código antigo) |
| `debug=True` / `CORS(app)` sem origem | limpo |
| MD5 / SHA1 / token falso | limpo (só menções em comentários) |
| `password` em serialização | limpo |
| `except:` nu | **0 ocorrências** |
| `@app.errorhandler` registrado | 3 |
| `datetime.utcnow()` | **0 ocorrências** |
| `Model.query.get/delete/count` | **0 ocorrências** |
| `type(x) ==` | **0 ocorrências** |
| Módulos sem importador | **nenhum** (menor contagem: 2) |

### Breaking changes

Três mudanças de contrato, todas correções de segurança, mais uma consequência
operacional:

1. **Autenticação obrigatória em 18 das 22 rotas.** Toda rota passa a exigir
   `Authorization: Bearer <token>`, exceto `POST /login`, `POST /users` (registro),
   `GET /` e `GET /health`. Sem token a resposta é `401`; com token de papel
   insuficiente, `403`. `DELETE /users/<id>` exige papel de administrador e
   `PUT /users/<id>` exige ser o próprio dono ou admin. Clientes que chamavam a
   API anonimamente precisam obter um token em `POST /login` e enviá-lo no header.

   Esta é a mudança de contrato mais larga da refatoração, e é a correção do
   finding 2. Ela tem exatamente a mesma natureza da remoção do campo `password`
   do item 2 abaixo: quebra quem dependia do comportamento inseguro, e é feita
   assim mesmo, porque o comportamento anterior *era* a vulnerabilidade. Não há
   variável de ambiente que a desligue — ver *Finding 2 — resolvido na segunda
   execução da skill*.

2. **`password` removido das respostas.** `GET /users/<id>`, `POST /users`,
   `PUT /users/<id>` e o objeto `user` de `POST /login` não devolvem mais o hash
   da senha. Clientes que liam esse campo deixam de recebê-lo.

3. **Política de senha de 4 para 8 caracteres mínimos.** `POST /users` e
   `PUT /users/<id>` passam a recusar com 400 senhas que antes eram aceitas. As
   senhas do seed mudaram de `1234`/`abcd`/`pass` para `senha1234`.

4. **Bancos existentes exigem novo seed ou reset de senha.** Os hashes MD5
   gravados não são verificáveis pelo scrypt: nenhum usuário pré-existente
   consegue autenticar sem ter a senha regravada. Para o ambiente de
   desenvolvimento, `python seed.py` resolve.

Mudanças que **não** quebram o contrato, mas vale registrar:

- O `token` de `POST /login` continua sendo uma string na mesma posição, mas agora é um JWT HS256 assinado com expiração, e não mais `'fake-jwt-token-<id>'`.
- Erros HTTP do próprio framework (415 por `Content-Type` ausente, 404 de rota inexistente, 405) agora respondem **JSON** `{"error": ...}` em vez da página HTML padrão do Flask. O status é preservado; só o corpo passa a ser consistente com o resto da API.
- Quatro entradas malformadas que devolviam 500 passam a devolver 400 (ver tabela acima).

### Ação pendente para o operador

O `SECRET_KEY` (`super-secret-key-123`) e a credencial de SMTP (`senha123`)
**continuam no histórico do Git**. Removê-los do código não os remove dos commits
anteriores: os dois valores precisam ser considerados comprometidos e
**rotacionados** na origem, não apenas substituídos por variáveis de ambiente.

---

## Segunda execução da skill

A primeira entrega recebeu uma devolutiva certeira: a infraestrutura de
autenticação estava bem construída, mas **desligada por default**
(`AUTH_REQUIRED=false` no `.env.example` e no `settings.py`), com todo guard do
`auth.py` barrando apenas quando a flag estivesse ligada. Resultado prático:
`DELETE /users/<id>` seguia aberto sem token — exatamente o impacto descrito no
CRITICAL 2 deste relatório, que o relatório dava como tratado.

A causa não estava no projeto, estava na skill. Por isso a correção começou por
ela, e só depois o projeto foi reprocessado.

### O que mudou na skill

| Arquivo | Mudança |
|---|---|
| `SKILL.md` — regra 4 | "Comportamento preservado" virou "**preservado, menos onde preservá-lo é preservar a falha**". A correção de segurança deixou de ser exceção tolerada e passou a ser obrigação, com a lista explícita do que entra — incluindo *exigir autenticação em rota que hoje responde sem credencial*. Um parágrafo novo proíbe nominalmente o padrão que causou o problema: **correção de segurança não fica atrás de flag desligada por default** (`AUTH_REQUIRED=false`, `ENABLE_AUTH=0`, `if (config.authEnabled)`) |
| `SKILL.md` — Fase 3, passo 5 | Duas justificativas passaram a ser recusadas explicitamente: *"resolver mudaria o contrato"* e *"o controle está implementado, basta ligar"*. Vale o comportamento com os defaults versionados, não o comportamento possível |
| `SKILL.md` — Fase 3, passo 6 | Nova exigência de validação: provar os controles **pela resposta**, chamando as rotas sensíveis sem credencial com a app subida nos defaults versionados, e colar os status |
| `references/refactoring-playbook.md` — RP-04 | Seção nova, *"Exigir o token é breaking change — e é para ser feito assim mesmo"*: o antes/depois do guard inerte vs. o guard incondicional, a tabela de escopo público mínimo, o texto pronto para a seção *Breaking changes* e o paralelo com o campo `password` |
| `references/antipattern-catalog.md` — AP-04 | Subseção *"Controle de acesso presente e desligado"*, com três greps de detecção e a instrução de tratar como CRITICAL, não como MEDIUM de configuração |
| `references/architecture-guidelines.md` — Config | "Defaults seguros" passou a incluir **autenticação exigida**, e ganhou a regra: configuração escolhe *qual* segredo e *qual* TTL, nunca *se* a verificação acontece |
| `references/report-template.md` | O exemplo de *Breaking changes* passou a incluir a exigência de token, e a lista de *erros que invalidam o relatório* ganhou o item: marcar como resolvido um finding de segurança cujo controle está desligado nos defaults |

A skill é idêntica nos três projetos (`code-smells-project/`,
`ecommerce-api-legacy/`, `task-manager-api/`) — as três cópias foram atualizadas.

### Fase 2 da segunda execução — o que a detecção nova encontrou

Os greps novos do AP-04 rodados contra o código então vigente:

```
$ grep -rniE "^\s*[A-Z_]*(AUTH|SECUR|GUARD)[A-Z_]*\s*=\s*(false|0|off|no)\s*$" .env.example
.env.example:21:AUTH_REQUIRED=false

$ grep -rniE "(getenv|environ\.get|_bool|boolean|env)\(\s*['\"][A-Z_]*(AUTH|SECUR|GUARD|PROTECT)['\"]..." .
src/config/settings.py:52:    AUTH_REQUIRED = _bool('AUTH_REQUIRED', 'false')

$ grep -rnE "if\s+\(?[a-z_.]*(settings|config|env)[a-z_.]*\.[A-Z_a-z]*(AUTH|auth)[A-Za-z_]*" .
src/middlewares/auth.py:35:            if settings.AUTH_REQUIRED and not payload:
src/middlewares/auth.py:52:            if settings.AUTH_REQUIRED:
src/middlewares/auth.py:68:    if settings.AUTH_REQUIRED and not payload:
src/middlewares/auth.py:88:            if settings.AUTH_REQUIRED:
src/middlewares/auth.py:114:            if settings.AUTH_REQUIRED:
```

Sete pontos: o default no `.env.example`, o default no módulo de config e os
cinco guards condicionados. Confirmado pela requisição real — as 22 rotas
respondendo sem nenhuma credencial:

```
--- LEITURAS (sem token) ---          --- ESCRITAS (sem token) ---
GET  /                     200        POST   /tasks           201
GET  /health               200        PUT    /tasks/1         200
GET  /tasks                200        DELETE /tasks/10        200
GET  /tasks/search         200        POST   /categories      201
GET  /tasks/stats          200        PUT    /categories/1    200
GET  /tasks/1              200        DELETE /categories/4    200
GET  /users                200        POST   /users           201
GET  /users/1              200        PUT    /users/1         200
GET  /users/1/tasks        200        POST   /login           200
GET  /categories           200
GET  /reports/summary      200        --- DESTRUTIVO ---
GET  /reports/user/1       200        DELETE /users/3         200
```

### Fase 3 da segunda execução — o que mudou no projeto

| Arquivo | Mudança |
|---|---|
| `src/config/settings.py` | `AUTH_REQUIRED` **removida**. Sobra `TOKEN_TTL_SECONDS`, que é parâmetro, não interruptor |
| `.env.example` | A variável saiu, substituída pelo comentário que explica que a autenticação não é opcional e quais são as 4 rotas públicas |
| `src/middlewares/auth.py` | Os cinco `if settings.AUTH_REQUIRED` sumiram; os guards valem sempre. Como nada mais era configurável, os decorators deixaram de receber `settings`: `require_auth` e `require_admin` viraram decorators diretos, e `require_self_or_admin`/`require_admin_for_role` mantêm só os próprios parâmetros. A lógica de identidade ficou num único `_require_identity()` |
| `src/views/routes.py` | As 10 rotas de leitura, antes abertas, passaram a exigir token. As 4 rotas públicas ficaram declaradas em `PUBLIC_ROUTES`, com o motivo de cada uma escrito ao lado — a decisão passa a ser legível no código, em vez de implícita na ausência de decorator |
| `src/app.py` | `build_blueprints(controllers, settings)` → `build_blueprints(controllers)`, já que `settings` virou parâmetro morto |
| `README.md` do projeto | Seção *Autenticação* reescrita: tabela das rotas públicas, exemplo de `curl` com token e a nota de por que não existe flag |

Escopo escolhido: **tudo autenticado, menos login, registro e liveness.** A
alternativa mais conservadora — exigir token só nas escritas — fecharia o
`DELETE /users/<id>` da devolutiva, mas deixaria `GET /users` devolvendo a lista
de e-mails de todos os usuários e `GET /reports/summary` devolvendo a produtividade
de cada um para qualquer anônimo. Os dois estão citados no *Impacto* do finding 2,
então parar nas escritas seria fechar o finding pela metade de novo.

### Validação da segunda execução

Todas as chamadas abaixo foram executadas com a aplicação subida nos defaults
versionados — sem `.env` local, exatamente o que se obtém clonando o repositório.

| Verificação | Resultado |
|---|---|
| Aplicação sobe sem erro | ✅ `python app.py` — sem traceback, `Debug mode: off`, ligada em `127.0.0.1` |
| Rotas registradas | ✅ 22 regras — as mesmas 22 de antes |
| Rotas protegidas sem token | ✅ 18/18 respondem `401` |
| Rotas públicas sem token | ✅ 4/4 respondem normalmente (`GET /` 200, `GET /health` 200, `POST /login` 200, `POST /users` 201) |
| Matriz de autorização | ✅ 17/17 — token ausente, adulterado, esquema errado, papel insuficiente, escalada de privilégio e caminhos permitidos |
| Contrato preservado sob token válido | ✅ **26/26** — status e forma de resposta idênticos à versão anterior rodando em paralelo na 5001, sobre bancos recém-seedados idênticos |
| `X-Total-Count` | ✅ presente e correto nas 5 listagens |
| `python seed.py` com `-W error::DeprecationWarning` | ✅ 3 usuários, 4 categorias, 10 tasks, sem warning |
| Varredura final dos sinais novos do AP-04 | ✅ 0 ocorrências em código executável (resta 1 menção em docstring, que documenta por que a flag não existe) |
| Imports mortos | ✅ nenhum novo (só os re-exports intencionais de `src/models/__init__.py`) |

**Comparação lado a lado, versão anterior (5001, sem token) × atual (5000, com token):**

```
idênticas: 26/26   divergentes: 0
```

Os 26 casos cobrem as 14 leituras, as 8 escritas, os 4 caminhos de erro
(`404` de recurso inexistente, `400` de validação, `401` de credencial inválida)
e a paginação. A única diferença de comportamento entre as duas versões é a
exigência do header — dado o token, a resposta é a mesma, campo a campo.

**Corpo das respostas de negação:**

```
$ curl -X DELETE http://127.0.0.1:5000/users/3
{"error":"Autenticação obrigatória"}

$ curl -X DELETE http://127.0.0.1:5000/users/3 -H "Authorization: Bearer <token de user comum>"
{"error":"Requer privilégio de administrador"}
```

Mesmo formato `{"error": ...}` do resto da API — a negação passa pelo error
handler central, não por um `return` solto no middleware.
