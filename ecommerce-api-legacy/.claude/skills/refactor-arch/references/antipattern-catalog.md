# Catálogo de anti-patterns

19 anti-patterns agrupados por severidade. Cada um traz **sinais de detecção acionáveis** (comando ou padrão de código), o **porquê** da severidade e o **padrão de correção** correspondente no `refactoring-playbook.md`.

Os sinais são escritos para Python e JavaScript porque são as stacks dos projetos-alvo, mas cada anti-pattern é definido de forma independente de linguagem — traduza o sinal para a stack detectada (o equivalente de `print()` em PHP é `echo`/`var_dump`, em Go é `fmt.Println`).

## Escala de severidade

| Nível | Critério |
|---|---|
| **CRITICAL** | Falha grave de arquitetura ou segurança: impede funcionamento correto, expõe dado sensível (credencial hardcoded, SQL Injection, senha vazada) ou viola completamente a separação de responsabilidades (God Class com banco + roteamento + negócio). |
| **HIGH** | Violação forte de MVC/SOLID que dificulta muito manutenção e teste: regra de negócio pesada dentro de controller, acoplamento forte sem injeção de dependência, estado global mutável, escrita multi-tabela sem transação. |
| **MEDIUM** | Padronização, duplicação ou gargalo de performance moderado: query N+1, listagem sem paginação, validação ausente na rota, middleware mal usado, API deprecated. |
| **LOW** | Legibilidade: magic numbers, nomenclatura ruim, `print` como log, imports e código mortos. |

**Regras de classificação:**
- **Exposição de dado sensível sobe para CRITICAL**, mesmo que o padrão base seja outro (um `console.log` é LOW; um `console.log` imprimindo número de cartão é CRITICAL).
- **Agrupe por raiz.** 15 ocorrências do mesmo `print()` são **um** finding com sub-itens, não 15 findings.
- Um achado que se encaixa em dois níveis sobe se tornar o código impossível de testar em isolamento ou se vazar dado.
- Só reporte o que você localizou fisicamente, com arquivo e linha.

---

# CRITICAL

## AP-01 — SQL Injection / query montada por concatenação

**Detecção**
```bash
grep -rnE "(execute|query|run|all|get)\(.*(\+|%s|%d|\$\{|f\"|f')" --include='*.py' --include='*.js' .
grep -rnE "(SELECT|INSERT|UPDATE|DELETE).*(\" *\+|' *\+|\$\{|% *\()" .
```
Sinais: `"SELECT * FROM t WHERE id = " + str(id)`, f-string com variável dentro de `execute()`, template literal `` `... ${x}` `` dentro de `db.run`, `.format()` em query, `%` formatting em query.

**Falso-positivo:** `?`/`%s` como *placeholder* passado no segundo argumento (`execute(sql, (id,))`, `db.run(sql, [id])`) é o uso **correto**. O que importa é o valor entrar pelo parâmetro, não pela string.

**Por que CRITICAL:** permite ler, alterar e apagar dados arbitrários. Em um `login`, um `' OR '1'='1` derruba a autenticação inteira. Agravante típico: o próprio projeto já usa placeholders em algum ponto (seed, migration), provando que a forma correta estava disponível.

→ Correção: **RP-01**

## AP-02 — Credenciais e segredos hardcoded

**Detecção**
```bash
grep -rniE "(secret|password|passwd|pwd|api[_-]?key|token|dbpass|private[_-]?key)\s*[:=]\s*['\"]" .
grep -rnE "(sk_live|pk_live|AKIA|Bearer |mongodb\+srv://|postgres://.*:.*@)" .
```
Sinais: `SECRET_KEY = 'minha-chave-123'`, `dbPass: "senha_prod"`, chave de gateway com prefixo `pk_live_`/`sk_live_`, credencial de SMTP no código, connection string com usuário e senha.

**Por que CRITICAL:** o segredo fica versionado no histórico do Git — rotacionar o valor não basta, o commit continua lá. Prefixo `_live_` indica credencial de produção, não sandbox.

**Sempre verifique junto:** `DEBUG = True` em código de produção (`app.run(debug=True, host='0.0.0.0')` expõe o console interativo do Werkzeug na rede) e `CORS(app)` sem restrição de origem.

→ Correção: **RP-02**

## AP-03 — God Class / God Module / God Method

**Detecção**
```bash
find . -name '*.py' -o -name '*.js' | xargs wc -l | sort -rn | head
grep -cE "def |function |=>" <arquivo_grande>
```
Sinais em um único arquivo/classe: cria a conexão de banco **e** define o schema **e** registra rotas **e** implementa a regra de negócio. Ou: um arquivo de model com mais de ~200 linhas atendendo 3+ domínios diferentes. Ou: um handler único com mais de ~60 linhas e mais de 3 níveis de aninhamento.

Heurística de contagem — conte quantas das responsabilidades abaixo o arquivo acumula. **3 ou mais = God Class**:
`(a)` conexão/config de banco · `(b)` DDL/schema/seed · `(c)` roteamento HTTP · `(d)` validação de entrada · `(e)` regra de negócio · `(f)` acesso a dados · `(g)` serialização de saída · `(h)` integração externa (pagamento, e-mail).

**Por que CRITICAL:** não há como testar a regra sem subir banco e servidor HTTP juntos; qualquer mudança tem raio de alcance sobre tudo. É a violação completa de separação de responsabilidades descrita na escala.

→ Correção: **RP-03**

## AP-04 — Autenticação quebrada / hashing de senha fraco

**Detecção**
```bash
grep -rniE "md5|sha1\(|\.hexdigest\(\)|base64|badCrypto|password ==|senha ==|pass ==" .
grep -rniE "fake.?(jwt|token)|token['\"]?\s*[:=].*\+\s*(str\()?.*id" .
```
Sinais: MD5/SHA1 como hash de senha (com ou sem salt), senha em texto puro no banco, comparação direta `user.password == pwd`, "criptografia" caseira (loop de base64, XOR, `substring`), token previsível (`'fake-jwt-token-' + user.id`), senha default silenciosa quando o campo vem vazio (`badCrypto(p || "123456")`).

**Por que CRITICAL:** MD5 sem salt cai por rainbow table em segundos e senhas iguais geram hashes iguais. Um token sem assinatura e sem expiração dá falsa impressão de autenticação onde não há nenhuma. Verifique também se existe alguma verificação de autorização: um método `is_admin()` definido e **nunca chamado** significa zero controle de acesso.

→ Correção: **RP-04**

## AP-05 — Exposição de dado sensível

**Detecção**
```bash
grep -rniE "'(password|senha|pass|token|secret)'\s*:" .          # campo em serialização de saída
grep -rniE "(console\.log|print|logger)\(.*(card|cc|cvv|password|senha|secret|key)" .
grep -rniE "@app\.route\(.*(admin|debug|query|reset)" .
```
Sinais: `to_dict()` / serializer incluindo `password`; `SECRET_KEY` devolvida por `/health`; número de cartão em log; endpoint que executa **SQL arbitrário** vindo do corpo da requisição; endpoint destrutivo (`reset-db`, `DELETE /all`) sem autenticação; stack trace completo na resposta de erro.

**Por que CRITICAL:** um endpoint de SQL arbitrário aberto não é sequer injeção — é console de banco público. PAN de cartão em log quebra PCI-DSS: todo coletor de log (arquivo, Docker, CloudWatch) passa a guardar o dado em claro.

→ Correção: **RP-02**, **RP-04**

---

# HIGH

## AP-06 — Regra de negócio dentro do controller / rota (ausência de camada de serviço)

**Detecção**
```bash
grep -rnE "@(app|bp)\.route|app\.(get|post|put|delete)\(" -A 40 . | grep -nE "SELECT|INSERT|if .*>|for .*in|\* 0\.|cursor"
```
Sinais: handler HTTP que faz SQL direto, calcula preço/desconto/imposto, monta o dicionário de resposta campo a campo e valida entrada — tudo no mesmo corpo de função. Um handler de 50+ linhas quase sempre é isso. Sintoma inverso: existe uma pasta `services/` e nenhum arquivo a importa.

**Por que HIGH:** a regra só é alcançável por requisição HTTP; não dá para testá-la nem reusá-la (job, CLI, worker). É a violação de MVC mais comum em projetos "parcialmente organizados".

→ Correção: **RP-05**

## AP-07 — Acoplamento forte / ausência de injeção de dependência

**Detecção**
```bash
grep -rnE "new sqlite3\.Database|sqlite3\.connect|createConnection|new .*Client\(" .
grep -rn "import " --include='*model*' --include='*service*' . | grep -iE "db|database|config"
```
Sinais: módulo instancia a própria conexão de banco (`this.db = new sqlite3.Database(...)` no construtor), service faz `import` direto do módulo de banco, `datetime.now()` chamado no meio da regra de negócio (impede testar data), cliente HTTP externo instanciado dentro da função que o usa.

**Por que HIGH:** trocar o banco, ou usar um fake em teste, exige reescrever o arquivo. Viola inversão de dependência (o "D" de SOLID).

→ Correção: **RP-06**

## AP-08 — Estado global mutável

**Detecção**
```bash
grep -rnE "^(let|var) [a-zA-Z_]+ *= *(\{\}|\[\]|0)" --include='*.js' .
grep -rnE "^[A-Za-z_]+ *= *(\{\}|\[\])" --include='*.py' .
grep -rn "global " --include='*.py' .
```
Sinais: `let globalCache = {}` exportado do módulo, acumulador global (`totalRevenue`), cache de módulo sem TTL nem limite de tamanho, `global x` em Python.

**Por que HIGH:** o estado é compartilhado entre requisições, o que gera resultado dependente de ordem, vazamento de memória (cache que só cresce) e testes que interferem uns nos outros. Armadilha adicional em CommonJS: **exportar um primitivo exporta uma cópia do valor** — `module.exports = { totalRevenue }` congela o valor no momento do import, então qualquer `totalRevenue += x` interno nunca é visto por quem importou.

→ Correção: **RP-07**

## AP-09 — Escrita multi-passo sem transação

**Detecção**
```bash
grep -rnE "INSERT INTO" -A 12 . | grep -cE "INSERT INTO"    # múltiplos INSERT encadeados no mesmo handler
grep -rniE "begin( transaction)?|commit|rollback|session\.begin|with .*transaction" .
```
Sinais: dois ou mais `INSERT`/`UPDATE` dependentes no mesmo fluxo (checkout: usuário → matrícula → pagamento → auditoria) sem `BEGIN`/`COMMIT`/`ROLLBACK`; `db.commit()` chamado a cada passo em vez de uma vez no fim; ausência de `FOREIGN KEY` nas `CREATE TABLE`; no SQLite, `FOREIGN KEY` declarada sem `PRAGMA foreign_keys = ON` (não é aplicada).

**Por que HIGH:** falha no passo 3 deixa os passos 1 e 2 gravados — aluno matriculado sem pagamento, pedido sem itens. O banco fica permanentemente inconsistente e o cliente recebe 500 como se nada tivesse acontecido. Confirmação típica no próprio código: um `DELETE` que responde "deletado, mas os registros relacionados ficaram sujos no banco".

→ Correção: **RP-09**

## AP-10 — Tratamento de erro ausente, engolido ou espalhado

**Detecção**
```bash
grep -rn "except:" --include='*.py' .            # except nu
grep -rnE "except Exception( as e)?:\s*(pass|$)" --include='*.py' .
grep -rnE "\(err[,)]" --include='*.js' . | wc -l   # compare com o nº de checagens de err
grep -rniE "errorhandler|app\.use\(\(err|middleware.*error" .
```
Sinais: `except:` nu (captura até `KeyboardInterrupt`/`SystemExit`); `catch` vazio; callback que recebe `err` e nunca o checa (`(err) => { res.send("ok") }`); `try/except` repetido em cada handler devolvendo `{'error': 'Erro interno'}, 500` **sem registrar stack trace**; nenhum `@app.errorhandler` / `app.use((err, req, res, next))` registrado.

**Por que HIGH:** o erro desaparece — sem stack trace no log e sem detalhe na resposta, o bug fica invisível em produção. Além disso, `err` ignorado em callback assíncrono vira `undefined` mais adiante e derruba o processo Node inteiro (`enrollments.length` de um `undefined`), fora de qualquer `try/catch`.

→ Correção: **RP-10**

---

# MEDIUM

## AP-11 — Query N+1

**Detecção**
```bash
grep -rnE "for .* in .*:" -A 8 --include='*.py' . | grep -E "execute|\.query\.|\.get\(|filter_by"
grep -rnE "\.(forEach|map)\(" -A 8 --include='*.js' . | grep -E "db\.(get|all|run)|SELECT"
```
Sinais: query dentro de laço; `User.query.get(x.user_id)` dentro de um `for` sobre a lista; `db.get(...)` dentro de `forEach`; contagem feita percorrendo registros em Python/JS em vez de `COUNT`/`GROUP BY`; ORM com relacionamento **declarado e não usado** (`task.user` existe no model, mas o código refaz `User.query.get(t.user_id)`); `len(u.tasks)` disparando lazy load por usuário.

**Cálculo do impacto (inclua no finding):** N registros com M relacionados = `1 + N + N*M` queries. Cite o número: *"20 cursos × 30 matrículas × 2 = 1.221 queries"*. Aninhamento em dois níveis é comum e multiplica.

**Agravante:** ausência de índice na chave estrangeira faz cada uma dessas queries ser um *full table scan*.

→ Correção: **RP-08**

## AP-12 — Listagem sem paginação nem limite

**Detecção**
```bash
grep -rnE "\.all\(\)|SELECT \* FROM [a-z_]+ *(;|\"|')" . | grep -viE "limit|offset|paginate"
grep -rnE "request\.args\.get\(.(page|limit|per_page)" .   # ausência é o sinal
```
Sinais: endpoint de listagem sem `LIMIT`/`OFFSET`, sem `paginate()`, sem parâmetros `page`/`limit`; relatório que varre a tabela inteira sem filtro de período; carregar todos os registros em memória para filtrar depois na aplicação (`[t for t in all_tasks if t.due_date < now]` no lugar de um `WHERE`).

**Por que MEDIUM:** a resposta cresce junto com a tabela, sem teto — funciona no seed com 5 linhas e derruba a aplicação com 500 mil.

→ Correção: **RP-16**

## AP-13 — Duplicação de regra de negócio e de validação

**Detecção**
```bash
grep -rn "def criar\|def atualizar\|def create_\|def update_" -A 30 .   # comparar blocos
grep -rniE "valid_status|VALID_|\[('|\")(pending|done|ativo)" . | sort | uniq -c | sort -rn
```
Sinais: o mesmo bloco de validação copiado entre `create` e `update`; a mesma regra ("está atrasada", "é elegível a desconto") reimplementada em 3+ handlers; o mesmo dicionário de serialização montado à mão em várias funções; o mesmo regex de e-mail em dois arquivos; listas literais de valores válidos (`['pending','done']`) repetidas dentro de handlers.

**Prova de que já divergiram** — sempre procure isto, é o argumento mais forte do finding: uma das cópias tem uma validação que a outra perdeu (dá para criar via `PUT` o que o `POST` recusa), ou um endpoint devolve um campo que o outro, para a mesma entidade, não devolve.

**Agravante frequente:** existe um método no model (`Task.is_overdue()`, `helpers.validate_email()`) que faz exatamente aquilo e **nunca é chamado** — a regra correta está escrita e ignorada.

→ Correção: **RP-11**

## AP-14 — Validação de entrada ausente ou superficial na rota

**Detecção**
```bash
grep -rnE "req\.body\.|request\.get_json\(\)|request\.json" -A 6 . | grep -viE "if not|schema|validate|marshmallow|joi|zod"
```
Sinais: leitura direta de `req.body.x` sem checar tipo nem formato; validação só de presença (`if (!u || !e)`) sem validar formato de e-mail, faixa numérica ou tipo; nenhum middleware de validação registrado; nenhuma biblioteca de schema (marshmallow, pydantic, joi, zod) usada apesar de declarada no manifesto.

**Por que MEDIUM:** um campo com tipo inesperado quebra a aplicação — `cc.startsWith(...)` lança `TypeError` se `card` vier como número, e em callback assíncrono isso derruba o processo. Validação espalhada por handler também é a origem do AP-13.

→ Correção: **RP-11**

## AP-15 — Uso de API deprecated ou removida *(checagem obrigatória)*

**Detecção** — rode a varredura completa abaixo e reporte cada ocorrência com a substituta:

```bash
grep -rnE "utcnow\(\)|datetime\.utcfromtimestamp|Query\.get\(|query\.get\(|before_first_request" --include='*.py' .
grep -rnE "new Buffer\(|url\.parse\(|\.substr\(|createCipher\(|require\('request'\)|util\.isArray" --include='*.js' .
```

| Stack | Deprecated | Substituto |
|---|---|---|
| Python 3.12+ | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)` |
| Python 3.12+ | `imp`, `distutils` | `importlib`, `setuptools`/`packaging` |
| Python | `assertEquals`, `@asyncio.coroutine` | `assertEqual`, `async def` |
| Flask 2.3+ | `@app.before_first_request` | inicialização no application factory |
| Flask | `flask.json.JSONEncoder`, `app.json_encoder` | `app.json_provider_class` |
| SQLAlchemy 2.0 | `Model.query.get(id)` | `db.session.get(Model, id)` |
| SQLAlchemy 2.0 | `Query.append_column`, `engine.execute()` | `select()` + `session.execute()` |
| Node 6+ | `new Buffer(x)` | `Buffer.from(x)` / `Buffer.alloc(n)` |
| Node | `url.parse()` | `new URL()` |
| Node | `crypto.createCipher` | `crypto.createCipheriv` |
| Node | `util.isArray`, `domain`, `fs.exists` | `Array.isArray`, `AsyncLocalStorage`, `fs.access` |
| Node | pacote `request` (deprecado desde 2020) | `fetch` nativo / `undici` / `axios` |
| JavaScript | `String.prototype.substr` | `.slice()` / `.substring()` |
| JavaScript | `escape()` / `unescape()` | `encodeURIComponent()` |
| Express 5 | `app.del()`, `res.send(status, body)`, `req.param()` | `app.delete()`, `res.status(s).send(b)`, `req.params/query/body` |
| Sequelize 6 | `Model.find()` | `Model.findOne()` |
| Bibliotecas | versão major EOL no manifesto (ex.: `flask-cors 4.x`, `moment`) | major suportada / `date-fns`, `Temporal` |

Verifique também no manifesto se alguma dependência está em versão sem suporte, e se o código usa uma API que a versão declarada já removeu.

**Se não encontrar nenhuma ocorrência, escreva explicitamente no relatório**: `Deprecated APIs: nenhuma ocorrência encontrada`. A checagem sempre aparece no relatório, mesmo negativa.

→ Correção: **RP-14**

---

# LOW

## AP-16 — Magic numbers e strings literais de domínio

**Detecção**
```bash
grep -rnE "(>|<|>=|<=|==) *[0-9]{2,}|\* *0\.[0-9]+|days=[0-9]+|priority *<= *[0-9]" .
grep -rnE "\[['\"](pending|done|ativo|admin|PAID)" .
```
Sinais: faixas de desconto (`if faturamento > 10000: desconto = faturamento * 0.1`), limites de tamanho (`len(titulo) > 200`), `timedelta(days=7)`, `if t.priority <= 2` codificando "alta prioridade" sem nome, listas literais de status/roles espalhadas.

**Agravante frequente:** o projeto **já tem** um bloco de constantes (`VALID_STATUSES`, `MAX_TITLE_LENGTH`) que ninguém importa, enquanto os literais seguem espalhados.

→ Correção: **RP-12**

## AP-17 — `print`/`console.log` como mecanismo de log

**Detecção**
```bash
grep -rn "print(" --include='*.py' . | grep -v test
grep -rn "console\.log(" --include='*.js' .
```
Sinais: `print`/`console.log` como único mecanismo de log — sem nível, timestamp ou destino configurável; log de dado pessoal (e-mail, CPF) em texto puro; `print("ENVIANDO EMAIL: ...")` **no lugar** de um efeito colateral real (a funcionalidade não existe, está fingida por um log).

**Sobe para CRITICAL** se o log imprime credencial, token ou dado de cartão (ver AP-05).

→ Correção: **RP-13**

## AP-18 — Nomenclatura ruim

**Detecção**
```bash
grep -rnE "(let|var|const) [a-z] *=|def [a-z]\(|\b(tmp|data2|aux|foo|obj)\b" .
```
Sinais: variáveis de uma letra em função longa (`u`, `e`, `p`, `cc`); abreviações inconsistentes que vazam para o **contrato público da API** (`usr`, `eml`, `pwd`, `c_id`); nome que sombreia builtin (`id`, `list`, `type` em Python); função com "and" no nome denunciando duas responsabilidades (`logAndCache`); `let` onde nunca há reatribuição; `const self = this` misturado com arrow functions no mesmo arquivo.

**Detalhe que eleva o finding:** quando a abreviação está no payload da API, corrigir é *breaking change* — registre isso.

→ Correção: **RP-15**

## AP-19 — Código morto: imports, funções e camadas não usadas

**Detecção**
```bash
# import declarado e símbolo nunca referenciado
grep -rn "^import \|^from .* import " --include='*.py' .
# módulo que ninguém importa
for f in $(find . -name '*.py' -path '*/services/*' -o -name '*.js' -path '*/utils/*'); do
  b=$(basename "$f" | sed 's/\..*//'); echo "$b: $(grep -rl "$b" --include='*.py' --include='*.js' . | grep -v "$f" | wc -l)"
done
```
Sinais: `import os, sys, json` sem nenhum uso; função utilitária definida e nunca chamada; **módulo inteiro que nenhum arquivo importa** (um `notification_service.py` pronto que a API nunca aciona — a funcionalidade de notificação simplesmente não existe); export de símbolo que ninguém consome; variável importada e não usada.

**Por que importa:** a pasta sugere uma arquitetura que o código não pratica, e o leitor seguinte acredita que a funcionalidade existe.

→ Correção: **RP-15**

---

## Checklist de varredura da Fase 2

Percorra os 19 na ordem e marque cada um como presente/ausente. Um projeto "organizado" (com `models/`, `routes/`, `services/`) normalmente concentra os achados em **AP-06, AP-10, AP-11, AP-13, AP-19** — não conclua que está limpo sem checar essas cinco explicitamente.

```
[ ] AP-01 SQL Injection            [ ] AP-08 Estado global mutável     [ ] AP-15 API deprecated (obrigatório)
[ ] AP-02 Segredos hardcoded       [ ] AP-09 Escrita sem transação     [ ] AP-16 Magic numbers
[ ] AP-03 God Class                [ ] AP-10 Erro engolido/espalhado   [ ] AP-17 print como log
[ ] AP-04 Auth quebrada            [ ] AP-11 Query N+1                 [ ] AP-18 Nomenclatura
[ ] AP-05 Dado sensível exposto    [ ] AP-12 Sem paginação             [ ] AP-19 Código/camada morta
[ ] AP-06 Regra no controller      [ ] AP-13 Duplicação de regra
[ ] AP-07 Sem injeção de dep.      [ ] AP-14 Validação ausente
```
