# Guidelines da arquitetura alvo (MVC)

O alvo é MVC em camadas, com dependências apontando sempre para dentro. As regras abaixo são independentes de linguagem; a estrutura de diretórios muda por stack, os papéis não.

---

## 1. As camadas e o que cada uma pode fazer

```
   Request
      │
      ▼
┌──────────────┐   só mapeia rota → controller; registra middlewares
│ Views/Routes │   NUNCA: SQL, regra de negócio, cálculo
└──────┬───────┘
       ▼
┌──────────────┐   orquestra: entrada validada → service → resposta HTTP
│ Controllers  │   NUNCA: SQL, regra de negócio, acesso direto a driver
└──────┬───────┘
       ▼
┌──────────────┐   regra de negócio pura, transações, orquestração de models
│  Services    │   NUNCA: request/response, status HTTP, jsonify/res.json
└──────┬───────┘
       ▼
┌──────────────┐   acesso a dados por entidade, queries parametrizadas,
│ Models/Repos │   serialização da entidade
└──────┬───────┘   NUNCA: request/response, regra de negócio de outro domínio
       ▼
    Database
```

**Regra da seta única:** cada camada só conhece a de baixo. Um model nunca importa um controller; um service nunca importa `flask.request` nem `express`. Se você precisou importar o framework HTTP dentro de um service, a fronteira está errada.

### Views / Routes
- Declaram caminho, método e o controller de destino. Uma linha por endpoint.
- Podem registrar middleware de validação e de autenticação por rota.
- Sem `try/except` por handler: o erro sobe para o error handler central.

### Controllers
- Uma função por endpoint. Tamanho alvo: **até ~15 linhas**.
- Fazem: ler entrada (params/body já validados), chamar **um** service, traduzir o retorno em status + corpo.
- Traduzem exceção de domínio em status HTTP (ou delegam isso ao error handler — escolha uma abordagem e use em todo o projeto).
- Não sabem que existe banco.

### Services
- Onde vive a regra de negócio: cálculo de desconto, elegibilidade, fluxo de checkout, "está atrasada".
- Recebem as dependências por injeção (repositório, gateway de pagamento, notificador, relógio).
- Abrem e fecham transação quando o fluxo escreve em mais de uma tabela.
- Lançam exceções de domínio (`ProdutoNaoEncontrado`, `PagamentoRecusado`), não retornam tuplas de HTTP.
- Testáveis sem servidor e sem banco real.

### Models / Repositories
- Um módulo por entidade (`produto_model.py`, `usuario_model.py`), nunca um arquivo com 4 domínios.
- Toda query parametrizada; nenhuma concatenação de string.
- Um único serializador por entidade — e ele **nunca** inclui campo sensível (senha, hash, token). Quando a saída precisa variar, use um schema de resposta separado do model.
- Com ORM: use os relacionamentos declarados e carregamento explícito (`joinedload`/`selectinload`) em vez de laço com query.

### Config
- Módulo único que lê variáveis de ambiente e expõe valores tipados.
- Zero segredo literal no código. `.env.example` versionado com chaves e valores fake; `.env` no `.gitignore`.
- Defaults seguros: `DEBUG=False`, CORS restrito, sem senha default, **autenticação exigida**.
- Nenhuma flag desliga um controle de segurança. Configuração escolhe *qual* segredo, *qual* origem, *qual* TTL — nunca *se* a verificação acontece. Se você se pegou escrevendo `if settings.AUTH_REQUIRED:` em volta de um `raise Unauthorized`, o `if` é o bug: o guard vale sempre, e o que sobra em ambiente é só o parâmetro (chave de assinatura, tempo de expiração).

### Middlewares
- **Error handler central** — captura exceção de domínio e não tratada, loga com stack trace, devolve corpo de erro padronizado. Nunca vaza stack trace na resposta.
- **Validação** — schema por endpoint, aplicado antes do controller.
- **Autenticação/autorização** — guard aplicado no mapeamento da rota (`views/`/`routes/`), nunca dentro do controller nem do service. Deny-by-default: o padrão é exigir credencial, e as rotas públicas são uma lista curta, nomeada e justificada no próprio arquivo de rotas. Se o projeto legado não tinha esta camada, ela é **criada** — a ausência não é um contrato a preservar. Ver RP-17.
- **Logging** — logger estruturado com nível; `print`/`console.log` não são log.

### Entry point / composition root
- Único lugar que **constrói** dependências concretas (conexão de banco, gateway, logger) e injeta nas camadas.
- Nenhum outro módulo instancia a própria conexão.
- Padrão: *application factory* (`create_app()` em Flask, `buildApp()` em Express) — deixa a aplicação montável em teste com dependências fake.

---

## 2. Estrutura de diretórios por stack

### Python / Flask

```
src/
├── config/
│   ├── __init__.py
│   └── settings.py           # lê env, valida obrigatórias
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── services/
│   ├── produto_service.py
│   └── pedido_service.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── views/
│   └── routes.py             # blueprints: rota → controller
├── middlewares/
│   ├── error_handler.py
│   └── validation.py
├── infrastructure/
│   └── database.py           # conexão + migrations, injetada
└── app.py                    # create_app() — composition root
app.py                        # entry point: from src.app import create_app
.env.example
```

Com Flask + SQLAlchemy, `models/` guarda as entidades do ORM e `repositories/` (ou métodos de query no próprio model) guarda o acesso — o importante é que a rota não faça `Model.query` diretamente.

### Node.js / Express

```
src/
├── config/index.js           # process.env, sem literal
├── models/                   # ou repositories/
│   ├── userRepository.js
│   └── courseRepository.js
├── services/
│   ├── checkoutService.js
│   └── reportService.js
├── controllers/
│   ├── checkoutController.js
│   └── reportController.js
├── routes/
│   └── index.js              # router.post('/api/checkout', ctrl.checkout)
├── middlewares/
│   ├── errorHandler.js       # app.use((err, req, res, next) => ...)
│   └── validate.js
├── infrastructure/
│   ├── database.js           # conexão, promisificada
│   └── paymentGateway.js     # interface + implementação
└── app.js                    # buildApp(deps) — composition root
server.js                     # entry point: buildApp().listen(config.port)
.env.example
```

### Outras stacks

Mesmos papéis, nomes idiomáticos da linguagem: Laravel `app/Http/Controllers` + `app/Models` + `app/Services` + `routes/`; Spring `controller/` + `service/` + `repository/` + `config/`; Django `views.py` (controller) + `models.py` + `services.py` + `urls.py`. **Siga a convenção do framework detectado** — não force nomes Flask em um projeto Express.

---

## 3. Convenções

- **Um arquivo, uma responsabilidade.** Alvo: model/service/controller até ~150 linhas. Passou disso, o domínio provavelmente comporta divisão.
- **Nomes por camada:** `<entidade>_model.py` / `<Entidade>Repository.js`, `<entidade>_service`, `<entidade>_controller`. O sufixo diz a camada.
- **Nomes de negócio, não abreviações:** `password`, não `pwd`; `courseId`, não `c_id`. Se a abreviação está no payload público da API, mantenha o campo antigo aceito e registre como breaking change planejado.
- **Constantes de domínio** em `config/constants.py` ou como `Enum` — nunca literais soltos no handler.
- **Idioma consistente:** se o projeto é em português, mantenha os nomes de domínio em português (`produto_model.py`). Não traduza entidades no meio da refatoração.

---

## 4. Checklist de conformidade da Fase 3

Cada item precisa ser verificável no código novo:

```
[ ] Diretórios seguem o padrão MVC da stack detectada
[ ] config/ lê 100% dos segredos de variável de ambiente; .env.example versionado
[ ] Nenhum literal de segredo restante no código  (grep do AP-02 limpo)
[ ] Um model por entidade; queries 100% parametrizadas
[ ] Serialização única por entidade, sem campo sensível
[ ] Services com regra de negócio, sem import do framework HTTP
[ ] Controllers com até ~15 linhas, sem SQL
[ ] Routes/Views só mapeiam rota → controller
[ ] Error handler central registrado; nenhum except nu / catch vazio
[ ] Middleware de validação nas rotas de escrita
[ ] Middleware de autenticação existe e é aplicado no mapeamento das rotas
[ ] Toda rota está classificada em público / autenticado / privilegiado, e a lista de públicas está escrita no arquivo de rotas
[ ] Nenhuma rota de relatório, faturamento, listagem de usuários ou escrita responde sem credencial
[ ] Nenhuma flag de ambiente desliga o guard (grep por AUTH_REQUIRED / ENABLE_AUTH limpo)
[ ] Entry point único constrói e injeta as dependências
[ ] Nenhum módulo instancia a própria conexão de banco
[ ] Nenhum estado global mutável
[ ] Escritas multi-tabela dentro de transação
[ ] Aplicação sobe sem erro
[ ] Endpoints originais respondem com mesmo status e mesma forma
```

---

## 5. Como validar (Fase 3, passo 6)

**Antes de refatorar**, capture a linha de base com a aplicação original; **depois**, repita exatamente as mesmas chamadas e compare.

```bash
# Python / Flask
python app.py &            # ou: flask --app src.app run
sleep 3
curl -s -o /dev/null -w "%{http_code} %{url_effective}\n" http://localhost:5000/produtos
curl -s http://localhost:5000/produtos/1 | head -c 400

# Node / Express
npm start &
sleep 3
curl -s -X POST http://localhost:3000/api/checkout \
  -H 'Content-Type: application/json' \
  -d '{"usr":"Guilherme","eml":"gui@x.com","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
```

**Matriz de acesso — obrigatória quando existe gate de autenticação (RP-17).** Uma linha por rota registrada, sem omitir nenhuma:

```bash
TOKEN_ADMIN=$(curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' \
  -d '{"email":"admin@loja.com","senha":"admin123"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')
TOKEN_CLIENTE=$(curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","senha":"123456"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

for rota in /produtos /usuarios /pedidos /relatorios/vendas; do
  printf '%-22s anon=%s cliente=%s admin=%s\n' "$rota" \
    "$(curl -s -o /dev/null -w '%{http_code}' localhost:5000$rota)" \
    "$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN_CLIENTE" localhost:5000$rota)" \
    "$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN_ADMIN" localhost:5000$rota)"
done
```

Confira o resultado contra o inventário: `401` onde o esperado é credencial, `403` onde o esperado é privilégio, `200` só nas públicas e nas autorizadas. Um `200` anônimo em rota classificada como autenticada invalida a validação inteira, por mais verde que esteja o resto.

- Enumere os endpoints a partir das rotas registradas; se o projeto tem `api.http`/`*.rest`/coleção Postman, use os payloads de lá.
- Compare **status** e **forma da resposta** (chaves do JSON), não valores voláteis (ids autoincrementais, timestamps).
- Encerre os processos que você subiu ao terminar.
- Diferença encontrada = corrigir e repetir. Só declare ✅ com a saída real em mãos.
