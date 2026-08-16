# Playbook de refatoração

16 transformações, uma por família de anti-pattern. Cada uma traz o padrão **antes → depois** em Python e/ou JavaScript. Os exemplos são ilustrativos: aplique o *padrão*, adaptado à linguagem e às convenções do projeto detectado.

| Padrão | Resolve |
|---|---|
| RP-01 Query parametrizada | AP-01 |
| RP-02 Config por variável de ambiente | AP-02, AP-05 |
| RP-03 Quebra da God Class em camadas | AP-03 |
| RP-04 Hashing forte + schema de resposta | AP-04, AP-05 |
| RP-05 Extração de service a partir do handler | AP-06 |
| RP-06 Injeção de dependência / composition root | AP-07 |
| RP-07 Eliminação de estado global | AP-08 |
| RP-08 N+1 → JOIN / eager loading / agregação | AP-11 |
| RP-09 Transação com rollback | AP-09 |
| RP-10 Error handler central | AP-10 |
| RP-11 Validação por schema reutilizado | AP-13, AP-14 |
| RP-12 Constantes nomeadas e Enums | AP-16 |
| RP-13 Logger estruturado | AP-17 |
| RP-14 Migração de API deprecated | AP-15 |
| RP-15 Renomeação e remoção de código morto | AP-18, AP-19 |
| RP-16 Paginação | AP-12 |

---

## RP-01 — Query parametrizada

**Antes**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
cursor.execute("... WHERE nome LIKE '%" + termo + "%'")
```

**Depois**
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
cursor.execute("SELECT * FROM produtos WHERE nome LIKE ?", (f"%{termo}%",))
```

```js
// antes
db.get(`SELECT * FROM courses WHERE id = ${cid}`, cb);
// depois
db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [courseId], cb);
```

Regras: o valor **sempre** entra pelo parâmetro. Em `LIKE`, os `%` fazem parte do *valor*, não da query. Identificador de tabela/coluna não pode ser parametrizado — se precisar de ordenação dinâmica, valide contra uma allowlist:

```python
COLUNAS_ORDENACAO = {"nome", "preco", "criado_em"}
if ordem not in COLUNAS_ORDENACAO:
    raise ValidacaoError("ordem inválida")
sql = f"SELECT * FROM produtos ORDER BY {ordem}"   # seguro: veio da allowlist
```

---

## RP-02 — Config por variável de ambiente

**Antes**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
CORS(app)
```
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_1234..." };
```

**Depois** — `src/config/settings.py`
```python
import os

class Settings:
    SECRET_KEY = os.environ["SECRET_KEY"]                    # obrigatória: falha no boot se faltar
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"    # default seguro
    DATABASE_PATH = os.getenv("DATABASE_PATH", "loja.db")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

settings = Settings()
```
```js
// src/config/index.js
require('dotenv').config();

function required(name) {
  const v = process.env[name];
  if (!v) throw new Error(`Variável de ambiente obrigatória ausente: ${name}`);
  return v;
}

module.exports = {
  port: Number(process.env.PORT || 3000),
  dbUrl: required('DATABASE_URL'),
  paymentGatewayKey: required('PAYMENT_GATEWAY_KEY'),
};
```

`.env.example` versionado (valores fake), `.env` no `.gitignore`. Segredo obrigatório deve **falhar no boot** quando ausente — melhor não subir do que subir com default inseguro.

Junto: remover endpoints que expõem configuração (`/health` devolvendo `SECRET_KEY` → devolver só `{"status": "ok"}`) e endpoints administrativos sem autenticação (`POST /admin/query` executando SQL arbitrário → **remover**; `POST /admin/reset-db` → remover ou exigir autenticação + confirmação).

> O segredo continua no histórico do Git. Registre no relatório que as credenciais expostas precisam ser **rotacionadas**, não apenas removidas do código.

---

## RP-03 — Quebra da God Class em camadas

**Antes** — `AppManager.js`: construtor abre o banco, `initDb()` cria schema e seed, `setupRoutes(app)` registra rotas com a regra de checkout inteira dentro do callback.

**Depois** — uma responsabilidade por arquivo:

```
src/
├── infrastructure/database.js       # conexão + migrations (era o construtor + initDb)
├── models/userRepository.js         # SELECT/INSERT de users
├── models/enrollmentRepository.js
├── services/checkoutService.js      # a regra que estava no callback da rota
├── controllers/checkoutController.js
├── routes/index.js                  # router.post('/api/checkout', ctrl.checkout)
└── app.js                           # buildApp(deps) — monta e injeta
```

Ordem da extração (de baixo para cima, testando a cada passo):
1. Extrair conexão e schema para `infrastructure/`.
2. Extrair as queries para um repositório por entidade.
3. Extrair a regra de negócio do corpo do handler para um service (RP-05).
4. Reduzir o handler a um controller de poucas linhas.
5. Mover o registro de rotas para `routes/`.
6. Montar tudo no composition root (RP-06) e apagar a classe antiga.

---

## RP-04 — Hashing forte + schema de resposta

**Antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
def to_dict(self):
    return {'id': self.id, 'name': self.name, 'password': self.password}   # vaza o hash
...
return jsonify({'token': 'fake-jwt-token-' + str(user.id)})
```
```js
function badCrypto(pwd) { /* base64 concatenado 10.000x, cortado em 10 chars */ }
let hash = badCrypto(p || "123456");   // senha default silenciosa
```

**Depois**
```python
import bcrypt

class User(db.Model):
    def set_password(self, raw: str) -> None:
        self.password_hash = bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()

    def check_password(self, raw: str) -> bool:
        return bcrypt.checkpw(raw.encode(), self.password_hash.encode())

    def to_dict(self) -> dict:                 # schema de saída: sem campo sensível
        return {'id': self.id, 'name': self.name, 'email': self.email, 'role': self.role}
```
```python
import jwt, datetime
token = jwt.encode(
    {"sub": user.id, "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)},
    settings.SECRET_KEY, algorithm="HS256",
)
```
```js
const bcrypt = require('bcrypt');
if (!password) throw new ValidationError('senha é obrigatória');   // nunca default silencioso
const hash = await bcrypt.hash(password, 12);
```

Junto: middleware de autenticação nas rotas de escrita, verificação de autorização de fato chamada (`is_admin()` que existe precisa ser usada), e resposta de login uniforme para e-mail inexistente e senha errada (evita enumeração de contas).

---

## RP-05 — Extração de service a partir do handler

**Antes** — rota faz tudo:
```python
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        tasks = Task.query.all()
        result = []
        for t in tasks:
            user = User.query.get(t.user_id)                    # N+1
            overdue = False
            if t.due_date:                                      # regra duplicada em 6 lugares
                if t.due_date < datetime.utcnow() and t.status != 'done':
                    overdue = True
            result.append({'id': t.id, 'title': t.title, 'user': user.name, 'overdue': overdue})
        return jsonify(result)
    except:
        return {'error': 'Erro interno'}, 500
```

**Depois** — três camadas:
```python
# src/models/task_model.py
class Task(db.Model):
    def is_overdue(self) -> bool:                     # regra única, já existia no model
        return bool(self.due_date) and self.due_date < now_utc() and self.status != Status.DONE

    def to_dict(self) -> dict:
        return {'id': self.id, 'title': self.title,
                'user': self.user.name, 'overdue': self.is_overdue()}

# src/services/task_service.py
class TaskService:
    def __init__(self, repository):
        self._repository = repository

    def list_tasks(self, page: int, per_page: int) -> list[dict]:
        tasks = self._repository.list_with_relations(page, per_page)   # eager loading
        return [t.to_dict() for t in tasks]

# src/controllers/task_controller.py
def list_tasks():
    page, per_page = get_pagination(request.args)
    return jsonify(task_service.list_tasks(page, per_page)), 200

# src/views/routes.py
task_bp.add_url_rule('/tasks', view_func=list_tasks, methods=['GET'])
```

O `try/except` sumiu: o erro sobe para o error handler central (RP-10).

---

## RP-06 — Injeção de dependência / composition root

**Antes**
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }   // acoplado ao SQLite
}
```

**Depois**
```js
// src/services/checkoutService.js
class CheckoutService {
  constructor({ userRepository, enrollmentRepository, paymentGateway, logger }) {
    this.users = userRepository;
    this.enrollments = enrollmentRepository;
    this.payments = paymentGateway;
    this.logger = logger;
  }
}

// src/app.js — composition root: único lugar que constrói o concreto
function buildApp({ db = createDatabase(config.dbUrl), gateway = new StripeGateway(config.paymentGatewayKey) } = {}) {
  const userRepository = new UserRepository(db);
  const checkoutService = new CheckoutService({ userRepository, paymentGateway: gateway, logger });
  const app = express();
  app.use(express.json());
  app.use(buildRoutes({ checkoutController: new CheckoutController(checkoutService) }));
  app.use(errorHandler);
  return app;
}
module.exports = { buildApp };

// server.js
buildApp().listen(config.port, () => logger.info(`up on ${config.port}`));
```

Em teste: `buildApp({ db: fakeDb, gateway: fakeGateway })` — nada de banco real. Em Python, o equivalente é o *application factory* `create_app(deps)`.

Integração externa também é dependência: `cc.startsWith("4") ? "PAID" : "DENIED"` dentro do handler vira uma interface `PaymentGateway` com implementação real e implementação fake para desenvolvimento.

---

## RP-07 — Eliminação de estado global

**Antes**
```js
let globalCache = {};
let totalRevenue = 0;
function logAndCache(key, data) { console.log(`[LOG] ${key}`); globalCache[key] = data; }
module.exports = { globalCache, totalRevenue, logAndCache };   // primitivo exportado por cópia
```

**Depois**
```js
// src/infrastructure/cache.js — instância injetada, com limite e TTL
class Cache {
  constructor({ ttlMs = 60_000, maxEntries = 1_000 } = {}) {
    this.ttlMs = ttlMs; this.maxEntries = maxEntries; this.store = new Map();
  }
  set(key, value) {
    if (this.store.size >= this.maxEntries) this.store.delete(this.store.keys().next().value);
    this.store.set(key, { value, expiresAt: Date.now() + this.ttlMs });
  }
  get(key) {
    const hit = this.store.get(key);
    if (!hit || hit.expiresAt < Date.now()) { this.store.delete(key); return undefined; }
    return hit.value;
  }
}
module.exports = { Cache };
```

`logAndCache` fazia duas coisas (o "and" no nome denunciava): virou `cache.set(...)` e `logger.info(...)`, separados. Acumuladores como `totalRevenue` viram consulta ao banco (`SUM`), não variável de módulo. Em Python, o equivalente é trocar `global x` e dicionários de módulo por atributo de instância de um serviço injetado.

---

## RP-08 — N+1 → JOIN, eager loading ou agregação

**Antes (SQL cru, 2 níveis)**
```python
for pedido in pedidos:                                   # 1 query
    cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(pedido["id"]))
    for item in cursor.fetchall():                       # N queries
        cursor.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))  # N*M
```
**Depois**
```python
cursor.execute("""
    SELECT p.id AS pedido_id, p.status, p.total,
           i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr    ON pr.id = i.produto_id
    WHERE p.usuario_id = ?
    ORDER BY p.id
    LIMIT ? OFFSET ?
""", (usuario_id, limit, offset))
# agrupa as linhas por pedido_id em memória — 1 query no lugar de 1 + N + N*M
```

**Depois (ORM — use os relacionamentos que já estão declarados)**
```python
from sqlalchemy.orm import joinedload
tasks = (Task.query
         .options(joinedload(Task.user), joinedload(Task.category))
         .limit(per_page).offset((page - 1) * per_page)
         .all())
```

**Contagem por grupo — deixe no banco**
```python
# antes: for user in users: len(Task.query.filter_by(user_id=user.id).all())
rows = (db.session.query(Task.user_id, func.count())
        .group_by(Task.user_id).all())
```

**Filtro — no WHERE, não em memória**
```python
# antes: [t for t in Task.query.all() if t.due_date < datetime.utcnow()]
overdue = Task.query.filter(Task.due_date < now_utc(), Task.status != Status.DONE).all()
```

**Callback aninhado (Node) → uma query + async/await**
```js
// antes: db.all(courses) → forEach → db.all(enrollments) → forEach → db.get(user) + db.get(payment)
//        com contadores manuais coursesPending/enrPending → race condition na ordem
const rows = await db.all(`
  SELECT c.id, c.title, u.name AS student, p.amount, p.status
  FROM courses c
  LEFT JOIN enrollments e ON e.course_id = c.id
  LEFT JOIN users u       ON u.id = e.user_id
  LEFT JOIN payments p    ON p.enrollment_id = e.id
  ORDER BY c.id
`);
// agrupa por curso; ordem determinística, erro propaga para o error handler
```

Acrescente índice nas chaves estrangeiras usadas no `JOIN`: `CREATE INDEX idx_itens_pedido_id ON itens_pedido(pedido_id);`

---

## RP-09 — Transação com rollback

**Antes** — quatro escritas encadeadas sem transação: se o `INSERT` de pagamento falha, a matrícula já gravada permanece.

**Depois**
```js
async function checkout({ userId, courseId, card }) {
  await db.run('BEGIN');
  try {
    const enrollmentId = await enrollments.create(userId, courseId);
    const payment = await gateway.charge({ card, amount: course.price });
    if (payment.status !== 'PAID') throw new PaymentDeclinedError();
    await payments.create(enrollmentId, course.price, payment.status);
    await auditLogs.create(`Checkout curso ${courseId} por ${userId}`);
    await db.run('COMMIT');
    return { enrollmentId };
  } catch (err) {
    await db.run('ROLLBACK');
    throw err;                       // sobe para o error handler
  }
}
```
```python
try:
    with db.session.begin():           # commit no sucesso, rollback na exceção
        pedido = repo.criar_pedido(...)
        repo.criar_itens(pedido.id, itens)
        repo.baixar_estoque(itens)
except IntegridadeError:
    raise EstoqueInsuficiente()
```

Junto: declarar `FOREIGN KEY ... ON DELETE CASCADE|RESTRICT` no schema e, em SQLite, habilitar `PRAGMA foreign_keys = ON` na abertura da conexão — sem o pragma, a FK declarada não é aplicada. Isso elimina o `DELETE` que deixa registros órfãos.

---

## RP-10 — Error handler central

**Antes**
```python
try:
    ...
except:                                    # nu: captura até KeyboardInterrupt
    return {'error': 'Erro interno'}, 500  # sem stack trace em lugar nenhum
```
```js
this.db.run(sql, [id], (err) => { res.send("Deletado"); });   // err ignorado
```

**Depois**
```python
# src/domain/errors.py
class DomainError(Exception):
    status_code = 400
class NotFoundError(DomainError):
    status_code = 404

# src/middlewares/error_handler.py
def register_error_handlers(app, logger):
    @app.errorhandler(DomainError)
    def handle_domain(err):
        logger.warning("domain error", exc_info=err)
        return {"error": str(err)}, err.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("erro não tratado")          # stack trace no log
        return {"error": "Erro interno"}, 500          # sem detalhe na resposta
```
```js
// src/middlewares/errorHandler.js — registrado por último, com 4 argumentos
function errorHandler(err, req, res, next) {
  logger.error({ err, path: req.path }, 'request failed');
  const status = err.statusCode || 500;
  res.status(status).json({ error: status === 500 ? 'Erro interno' : err.message });
}
```

Com isso, os `try/except` por handler desaparecem. Em callbacks Node, todo `err` é checado — ou, melhor, a API vira `Promise` (RP-14) e o `throw` chega ao handler via `next(err)`/`express-async-errors`.

---

## RP-11 — Validação por schema reutilizado

**Antes** — o mesmo bloco copiado entre `criar` e `atualizar`, já divergido (a versão do `PUT` perdeu duas regras).

**Depois**
```python
# src/schemas/produto_schema.py
from marshmallow import Schema, fields, validate
from src.config.constants import CATEGORIAS_VALIDAS, MAX_NOME_PRODUTO

class ProdutoSchema(Schema):
    nome      = fields.Str(required=True, validate=validate.Length(min=1, max=MAX_NOME_PRODUTO))
    preco     = fields.Float(required=True, validate=validate.Range(min=0))
    estoque   = fields.Int(required=True, validate=validate.Range(min=0))
    categoria = fields.Str(required=True, validate=validate.OneOf(CATEGORIAS_VALIDAS))

class ProdutoUpdateSchema(ProdutoSchema):
    class Meta:
        partial = True          # PUT parcial reaproveita as MESMAS regras
```
```python
# src/middlewares/validation.py
def validate_body(schema):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                kwargs["data"] = schema().load(request.get_json() or {})
            except ValidationError as err:
                return {"errors": err.messages}, 422
            return fn(*args, **kwargs)
        return wrapper
    return decorator
```
```js
// Express + zod
const checkoutSchema = z.object({
  userName: z.string().min(1),
  email: z.string().email(),
  password: z.string().min(8),
  courseId: z.number().int().positive(),
  cardNumber: z.string().regex(/^\d{13,19}$/),   // garante string: mata o TypeError de cc.startsWith
});
router.post('/api/checkout', validate(checkoutSchema), ctrl.checkout);
```

Regras de negócio que não são formato (ex.: "está atrasada") vão para um método único do model/service, chamado por todos os pontos — nunca reimplementado por handler.

---

## RP-12 — Constantes nomeadas e Enums

**Antes**
```python
if faturamento > 10000:   desconto = faturamento * 0.1
elif faturamento > 5000:  desconto = faturamento * 0.05
if t.priority <= 2:  ...            # "alta prioridade" implícito
if status not in ['pending', 'in_progress', 'done']:  ...
```

**Depois**
```python
# src/config/constants.py
FAIXAS_DESCONTO = (            # (faturamento mínimo, percentual)
    (10_000, 0.10),
    ( 5_000, 0.05),
    ( 1_000, 0.02),
)
PRIORIDADE_ALTA_ATE = 2
MAX_TITULO = 200

class Status(str, Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    DONE = 'done'
```
```python
def calcular_desconto(faturamento: float) -> float:
    for minimo, percentual in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * percentual
    return 0.0
```

Se o projeto **já tem** um bloco de constantes que ninguém importa, a correção é usá-lo (movendo-o para `config/`), não criar um terceiro.

---

## RP-13 — Logger estruturado

**Antes**
```python
print("Buscando produto " + str(id))
print("ENVIANDO EMAIL: " + usuario['email'])     # efeito colateral fingido por log
```
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);  // PAN + chave em log
```

**Depois**
```python
# src/infrastructure/logger.py
import logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)
logger = logging.getLogger("app")

logger.debug("buscando produto", extra={"produto_id": produto_id})
logger.error("falha ao criar pedido", exc_info=True)
```
```js
const pino = require('pino');
const logger = pino({ level: process.env.LOG_LEVEL || 'info' });
logger.info({ courseId, userId }, 'checkout iniciado');   // sem PAN, sem chave
```

Regras: nunca logar credencial, token, senha ou número de cartão (mascare: `**** **** **** 4444`); evitar dado pessoal em log de nível `info`; `print` que **substituía** funcionalidade (envio de e-mail) vira um serviço de verdade (`NotificationService`) injetado — ou é removido, se a funcionalidade não existe mesmo. Se o projeto já tem um `services/notification_service.py` que ninguém importa, ligue-o ao fluxo ou remova-o; não deixe camada morta.

---

## RP-14 — Migração de API deprecated

```python
# antes                                    # depois
datetime.utcnow()                          datetime.now(timezone.utc)
Model.query.get(id)                        db.session.get(Model, id)
@app.before_first_request                  inicialização dentro de create_app()
type(tags) == list                         isinstance(tags, list)
```
```js
// antes                                   // depois
new Buffer(x)                              Buffer.from(x)
url.parse(u)                               new URL(u)
str.substr(0, 10)                          str.slice(0, 10)
crypto.createCipher(...)                   crypto.createCipheriv(...)
require('request')                         fetch (nativo) / undici
res.send(404, 'x')                         res.status(404).send('x')
```

**Callback → Promise/async-await** (elimina os contadores manuais e a race condition do AP-11/AP-10):
```js
// antes
db.all(sql, [], (err, rows) => { ... });

// depois — src/infrastructure/database.js
const { promisify } = require('util');
db.allAsync = promisify(db.all.bind(db));
db.getAsync = promisify(db.get.bind(db));
db.runAsync = promisify(db.run.bind(db));   // atenção: para lastID, use wrapper com function(err){this.lastID}

const rows = await db.allAsync(sql);        // erro propaga para o error handler
```

Ao migrar, confira a versão declarada no manifesto: se o código usa API que a versão já removeu, é bug latente, não só depreciação.

---

## RP-15 — Renomeação e remoção de código morto

**Antes**
```js
let u = req.body.usr;  let e = req.body.eml;  let p = req.body.pwd;
let cid = req.body.c_id;  let cc = req.body.card;
const self = this;
```
**Depois**
```js
const { userName, email, password, courseId, cardNumber } = req.validated;
```

- `e` é especialmente perigoso em JS: é a convenção universal de `error`/`event`.
- `self = this` some ao trocar `function(err)` por arrow function ou async/await.
- Abreviação no **payload público** (`usr`, `eml`, `c_id`) é breaking change: aceite os dois nomes por um período (`req.body.userName ?? req.body.usr`) e registre a mudança no relatório e no README.
- Remova import não usado, função nunca chamada e export que ninguém consome. Confirme com grep antes de apagar — um símbolo pode ser usado por reflexão ou por nome em string.
- Módulo em `services/`/`utils/` que ninguém importa: ligue ao fluxo ou remova. Manter é pior — sugere uma funcionalidade que não existe.

---

## RP-16 — Paginação

**Antes**
```python
@app.route('/pedidos')
def listar():
    return jsonify(models.get_todos_pedidos())    # tabela inteira, sem teto
```
**Depois**
```python
# src/middlewares/pagination.py
MAX_PER_PAGE = 100
def get_pagination(args):
    page = max(1, int(args.get('page', 1)))
    per_page = min(MAX_PER_PAGE, max(1, int(args.get('per_page', 20))))
    return page, per_page
```
```python
def list_pedidos():
    page, per_page = get_pagination(request.args)
    itens, total = pedido_service.listar(page, per_page)
    return jsonify({
        "data": itens,
        "meta": {"page": page, "per_page": per_page, "total": total},
    }), 200
```
```sql
SELECT ... FROM pedidos ORDER BY id LIMIT ? OFFSET ?
```

Se a resposta original era um array puro e o consumidor depende disso, mantenha o array e envie a paginação em headers (`X-Total-Count`, `Link`) — assim a paginação entra **sem** quebrar o contrato. Escolha uma das duas formas e aplique em todas as listagens.

---

## Ordem de aplicação recomendada

1. **RP-02** (config/segredos) — desbloqueia todo o resto e não quebra nada.
2. **RP-01, RP-04** (segurança de dados) — CRITICAL, mudanças locais.
3. **RP-03, RP-06** (estrutura + injeção) — cria os diretórios e o composition root.
4. **RP-05** (services) — move a regra para fora dos handlers.
5. **RP-10, RP-11, RP-09** (erro, validação, transação) — transversais, aplicados sobre a estrutura nova.
6. **RP-08, RP-16** (performance) — precisam da camada de dados já isolada.
7. **RP-07, RP-12, RP-13, RP-14, RP-15** (limpeza) — por último, com a validação rodando a cada passo.

Valide o boot e os endpoints **a cada grupo**, não só no fim: assim uma quebra é atribuível ao passo que a causou.
