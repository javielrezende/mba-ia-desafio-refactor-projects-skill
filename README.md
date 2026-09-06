# Criação de Skills — Refatoração Arquitetural Automatizada

Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Contexto

### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Nota sobre a ferramenta:** Os exemplos deste documento usam o Claude Code (`.claude/skills/`) como referência, pois é a ferramenta utilizada no curso. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

## Requisitos

### 1. Análise Manual dos Projetos

Antes de criar a skill, você deve entender os problemas que ela vai resolver.

**Tarefas:**

- Analisar o projeto `code-smells-project/` (Python/Flask — API de E-commerce)
- Analisar o projeto `ecommerce-api-legacy/` (Node.js/Express — LMS API com fluxo de checkout)
- Analisar o projeto `task-manager-api/` (Python/Flask — API de Task Manager)

Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

- 1 de severidade CRITICAL ou HIGH
- 2 de severidade MEDIUM
- 2 de severidade LOW

Documentar os achados na seção "Análise Manual" do seu `README.md`

> **Dica:** Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural. Use os projetos como insumo para entender quais padrões sua skill precisa detectar.

> **Por que 3 projetos?** Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia — lidando tanto com código completamente desestruturado quanto com projetos que já possuem alguma separação de camadas.

### 2. Criação da Skill

Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

**Tarefas:**

Criar a skill dentro do projeto `code-smells-project/` e implementar o SKILL.md com 3 fases sequenciais:

- **Fase 1 — Análise:** Detectar stack, mapear arquitetura atual, imprimir resumo
- **Fase 2 — Auditoria:** Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
- **Fase 3 — Refatoração:** Reestruturar para o padrão MVC, validar que funciona

Criar arquivos de referência em Markdown que forneçam à skill o conhecimento necessário para executar as 3 fases. Os arquivos devem cobrir **obrigatoriamente** as seguintes áreas de conhecimento:

| Área de conhecimento | O que deve conter |
|---|---|
| Análise de projeto | Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura |
| Catálogo de anti-patterns | Anti-patterns com sinais de detecção e classificação de severidade |
| Template de relatório | Formato padronizado do relatório de auditoria (Fase 2) |
| Guidelines de arquitetura | Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers, responsabilidades de cada uma) |
| Playbook de refatoração | Padrões concretos de transformação para cada anti-pattern (com exemplos de código) |

> **Nota:** Você tem liberdade para organizar os arquivos de referência como preferir — pode usar os nomes e a quantidade de arquivos que fizer sentido para sua skill. O importante é que todas as 5 áreas de conhecimento estejam cobertas. O nome da skill (`refactor-arch`) e o arquivo `SKILL.md` são obrigatórios e não devem ser alterados. O path da skill segue a convenção da ferramenta escolhida (no Claude Code, por exemplo, é `.claude/skills/refactor-arch/`).

**Requisitos da skill:**

- Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos, independente da stack ou nível de organização
- O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
- O catálogo deve incluir detecção de APIs deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno
- O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
- A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
- A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)

### 3. Execução da Skill

Execute sua skill nos 3 projetos e valide que ela funciona em todas as stacks.

#### Projeto 1 — code-smells-project (Python/Flask)

Invocar a skill no Claude Code:

```bash
claude "/refactor-arch"
```

> **Nota:** O comando acima é o exemplo com Claude Code. Se você estiver usando Gemini CLI ou Codex, utilize o comando equivalente para invocar uma skill na sua ferramenta.

- Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
- Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
- Confirmar a execução da Fase 3
- Verificar que a Fase 3:
  - Cria a estrutura de diretórios baseada em MVC
  - A aplicação inicia sem erros
  - Os endpoints originais continuam respondendo
- Salvar o relatório de auditoria (output da Fase 2) em `reports/audit-project-1.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

Prove que sua skill é reutilizável em outro projeto de backend, mas com stack diferente.

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `ecommerce-api-legacy/`
- Invocar a skill:

```bash
cd ../ecommerce-api-legacy
claude "/refactor-arch"
```

- Verificar que as 3 fases executam corretamente neste projeto
- Salvar o relatório em `reports/audit-project-2.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 3 — task-manager-api (Python/Flask)

Agora o teste com um projeto Python/Flask que já possui alguma organização de camadas (models, routes, services, utils).

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `task-manager-api/`
- Invocar a skill:

```bash
cd ../task-manager-api
claude "/refactor-arch"
```

- Verificar que:
  - A Fase 1 detecta corretamente Python/Flask como stack e identifica o domínio de Task Manager
  - A Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
  - A Fase 3 melhora a estrutura sem quebrar a aplicação (todos os endpoints devem continuar respondendo)
- Salvar o relatório em `reports/audit-project-3.md`
- Commitar o código refatorado do projeto no repositório

> **Nota:** Este projeto já possui alguma separação de camadas, mas isso não significa que a arquitetura está adequada. A skill deve identificar tanto problemas de código (segurança, performance, qualidade) quanto oportunidades de melhoria arquitetural. Se houver mudanças estruturais necessárias, a skill deve propô-las e executá-las.

#### Validação

Para cada projeto refatorado, valide o seguinte checklist:

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

> **Dica:** Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Entregável

Repositório público no GitHub (fork do repositório base) contendo:

- Skill completa em `.claude/skills/refactor-arch/` (dentro dos 3 projetos)
- Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
- Relatórios de auditoria em `reports/` (3 arquivos)
- `README.md` atualizado

### Estrutura do repositório

Faça um fork do repositório base contendo os três projetos com code smells.

> **Nota:** A estrutura abaixo usa Claude Code como exemplo (`.claude/skills/`). Se estiver usando outra ferramenta, adapte os caminhos conforme a convenção dela.

```
desafio-skills/
├── README.md                              # Sua documentação
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (API de E-commerce)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← SUA SKILL AQUI
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS API com checkout)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── src/
│   │   ├── app.js
│   │   ├── AppManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (API de Task Manager)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── app.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/                               # Relatórios gerados
    ├── audit-project-1.md                 # Saída da Fase 2 no projeto 1
    ├── audit-project-2.md                 # Saída da Fase 2 no projeto 2
    └── audit-project-3.md                 # Saída da Fase 2 no projeto 3
```

**O que você vai criar:**

- `.claude/skills/refactor-arch/` — A skill completa (SKILL.md + arquivos de referência)
- Código refatorado dos 3 projetos — resultado da execução da Fase 3, commitado no repositório
- `reports/audit-project-{1,2,3}.md` — Relatório de auditoria de cada projeto
- `README.md` — Documentação do seu processo

**O que já vem pronto:**

- `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
- `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
- `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade

> **Dica:** Cada projeto contém problemas intencionais de diferentes severidades (CRITICAL, HIGH, MEDIUM, LOW), incluindo falhas de segurança, violações arquiteturais e problemas de qualidade de código. Parte do desafio é identificá-los por conta própria através da análise manual do código.

### README.md deve conter

**A) Seção "Análise Manual":**

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

### Ordem de execução sugerida

**1. Analisar os projetos manualmente**

Leia o código dos três projetos e documente os problemas encontrados.

**2. Criar a skill**

Escreva o SKILL.md e os arquivos de referência.

**3. Executar nos 3 projetos**

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Salve a saída da Fase 2 de cada projeto em `reports/audit-project-{1,2,3}.md`.

**4. Iterar**

Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Critérios de Aceite

A skill deve atingir os seguintes mínimos em **todos os 3 projetos**:

| Critério | Requisito |
|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) |

**IMPORTANTE:** Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

> **Sobre o projeto 3 (task-manager-api):** Este projeto já possui alguma organização. "aplicação funciona" significa que a API inicia sem erros e todos os endpoints continuam respondendo corretamente.

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills

---

## Dicas Finais

- **Comece pela análise manual** — entender os problemas profundamente é essencial para criar uma skill que os detecte.
- **O SKILL.md é um prompt** — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
- **Seja específico nos sinais de detecção** — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
- **Teste incrementalmente** — não tente criar a skill perfeita de primeira.
- **A skill deve ser copiável** — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
- **Projetos diferentes exigem adaptação** — a Fase 3 de um projeto já parcialmente organizado não vai ter as mesmas transformações de um monolito. Sua skill deve se adaptar ao contexto.
- **Pedir confirmação na Fase 2 é obrigatório** — o humano deve revisar o relatório antes de qualquer modificação.
- **Consulte as referências do curso** — revise a documentação oficial da ferramenta escolhida e os materiais das aulas para relembrar a estrutura e anatomia de uma skill.

---

## Análise Manual

Leitura manual do código, sem ferramenta automatizada. Achados listados por severidade, com arquivo/linha e o motivo de cada um ser relevante.

### Projeto 1 — `code-smells-project/` (Python/Flask — API de E-commerce)

**Estrutura atual:** 4 arquivos na raiz — `app.py` (rotas), `controllers.py` (handlers), `models.py` (acesso a dados), `database.py` (conexão + schema + seed). Existe uma separação nominal de camadas, mas ela vaza em vários pontos.

---

#### 1. [CRITICAL] SQL Injection — queries montadas por concatenação de string

**Onde:** `models.py` — praticamente todas as funções. Exemplos:
- `models.py:28` — `"SELECT * FROM produtos WHERE id = " + str(id)`
- `models.py:47-50` — `INSERT INTO produtos ... VALUES ('" + nome + "', '" + descricao + "', ...`
- `models.py:109-111` — `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`
- `models.py:291` — `" AND (nome LIKE '%" + termo + "%' ...)"`

**Por que é relevante:** o banco é SQLite via `sqlite3`, que suporta *placeholders* (`?`) — e o próprio `database.py:70-73` já usa `executemany` com `?` no seed, ou seja, a forma correta existe no projeto e simplesmente não foi usada no resto. O caso mais grave é o `login_usuario`: uma senha como `' OR '1'='1` derruba a autenticação inteira e devolve o primeiro usuário da tabela (que no seed é o **admin**, `database.py:76`). Nos endpoints de escrita a concatenação permite terminar a query e alterar/apagar dados. É o equivalente exato ao `mysql_query("SELECT ... WHERE id = $_GET['id']")` que se aprende que nunca deve ser escrito — aqui está em ~15 lugares.

**Agravantes na mesma família (mesma raiz, mesma correção de rota):**
- `app.py:59-78` — endpoint `POST /admin/query` executa **SQL arbitrário** enviado no corpo da requisição, sem autenticação. Não é nem injeção: é um console de banco aberto na internet.
- `app.py:47-57` — `POST /admin/reset-db` apaga as 4 tabelas, também sem autenticação.
- `app.py:7` / `controllers.py:289` — `SECRET_KEY` hardcoded no código **e devolvida em texto puro** pelo `/health`, junto com `debug: True` e o caminho do banco. Endpoint de health check é tipicamente público.
- Senhas gravadas e comparadas em texto puro (`database.py:76-78`, `models.py:110`) e o `/usuarios` devolve o campo `senha` de todos os usuários no JSON (`models.py:83`).

**Correção esperada:** queries parametrizadas em 100% dos acessos, hash de senha (bcrypt/argon2), remoção dos endpoints `/admin/*` (ou autenticação + autorização real), `SECRET_KEY` e `DEBUG` vindos de variável de ambiente, e o campo `senha` fora de qualquer serialização de saída.

---

#### 2. [MEDIUM] Query N+1 na listagem de pedidos

**Onde:** `models.py:171-201` (`get_pedidos_usuario`) e `models.py:203-233` (`get_todos_pedidos`) — o mesmo trecho, duplicado.

**Por que é relevante:** o padrão é o clássico N+1, aqui em **dois níveis aninhados**. Para cada pedido abre-se um cursor e uma query nova para buscar os itens (`models.py:188`), e **para cada item** abre-se mais um cursor e mais uma query para buscar o nome do produto (`models.py:192`). Uma listagem de 50 pedidos com 4 itens cada dispara `1 + 50 + 200 = 251` queries onde um único `SELECT` com dois `JOIN` (`pedidos` → `itens_pedido` → `produtos`) resolveria. O `GET /pedidos` não tem paginação nem `LIMIT` (`models.py:206`), então o custo cresce linearmente com a tabela inteira e não tem teto. Some-se a isso que não há índice em `itens_pedido.pedido_id` nem em `itens_pedido.produto_id` (`database.py:45-53`): cada uma das 250 queries é um *full table scan*.

**Correção esperada:** substituir os loops por uma query única com `JOIN` e agrupar o resultado em memória; adicionar índices nas chaves estrangeiras; introduzir paginação nos endpoints de listagem.

---

#### 3. [MEDIUM] Validação duplicada no controller e mapeamento de linha repetido no model

**Onde:**
- `controllers.py:28-54` vs `controllers.py:72-90` — o bloco de validação de produto (campos obrigatórios, preço/estoque negativos, tamanho do nome) está copiado e colado entre `criar_produto` e `atualizar_produto`.
- `models.py:12-21`, `models.py:31-40` e `models.py:304-313` — o mesmo dicionário de 8 campos de produto é montado à mão em três funções distintas.

**Por que é relevante:** são duas cópias que já começaram a divergir — o `atualizar_produto` **perdeu** a validação de tamanho do nome e a de categoria válida (`controllers.py:47-54`), presentes só na criação. Ou seja, dá para criar um produto com categoria inválida via `PUT` mas não via `POST`. É exatamente o sintoma que a duplicação produz: a regra vive em dois lugares, alguém corrige um e esquece o outro. O mesmo vale para o mapeamento de colunas — adicionar um campo em `produtos` exige lembrar de editar três funções, e esquecer uma gera respostas inconsistentes entre `GET /produtos` e `GET /produtos/busca`.

Vale registrar também que a lista de categorias válidas (`controllers.py:52`) e a de status de pedido (`controllers.py:242`) estão como *arrays* literais dentro do handler HTTP — regra de negócio dentro do controller, sem fonte única de verdade.

**Correção esperada:** extrair um validador/*schema* de produto reutilizado pelos dois handlers, um serializador único por entidade no model, e mover as listas de valores válidos para constantes/enums de domínio.

---

#### 4. [LOW] Magic numbers na regra de desconto do relatório

**Onde:** `models.py:256-262`.

```python
if faturamento > 10000:
    desconto = faturamento * 0.1
elif faturamento > 5000:
    desconto = faturamento * 0.05
elif faturamento > 1000:
    desconto = faturamento * 0.02
```

**Por que é relevante:** cinco números soltos codificando uma política comercial, sem nenhuma constante nomeada ou comentário explicando de onde vêm. Não dá para saber, lendo o código, se `0.05` é uma faixa de desconto por volume, uma comissão ou um imposto — o nome da variável (`desconto`) é a única pista. Quando o time comercial mudar a faixa, alguém precisa caçar o número no meio da função de relatório. É o tipo de constante que deveria estar nomeada (`FAIXAS_DESCONTO`) e, idealmente, fora do model.

**Correção esperada:** extrair as faixas para constantes nomeadas ou uma estrutura de configuração, e mover o cálculo para uma camada de serviço/domínio.

---

#### 5. [LOW] `print()` como log e concatenação manual de strings

**Onde:** espalhado — `controllers.py:8`, `:11`, `:57`, `:61`, `:106`, `:161`, `:179`, `:182`, `:208-210`, `:219`, `:248`, `:250`; `app.py:56`, `:83-86`; `database.py` (indireto).

**Por que é relevante:** três problemas juntos no mesmo padrão. (a) `print()` não tem nível de severidade, timestamp nem destino configurável — em produção vai para o *stdout* e some; não dá para filtrar erro de informação. (b) A concatenação `"texto " + str(x)` é verbosa e frágil comparada a f-strings, e aparece em ~20 lugares. (c) Vários desses `print` estão **logando dado sensível ou substituindo funcionalidade**: `controllers.py:161` e `:179` registram o e-mail do usuário em log de texto puro, e `controllers.py:208-210` usa `print("ENVIANDO EMAIL: ...")` no lugar de um disparo real de notificação — um efeito colateral de negócio que nunca acontece, disfarçado de log.

Na mesma linha de legibilidade: o parâmetro `id` (`controllers.py:14`, `models.py:24`) sombreia a *builtin* `id()` do Python, e `models.py:2` importa `sqlite3` sem usar.

**Correção esperada:** substituir `print` pelo módulo `logging` com níveis apropriados, adotar f-strings, remover dado pessoal dos logs, e extrair as notificações para um serviço próprio (mesmo que *stub*) em vez de deixá-las como texto impresso no controller.

---

**Resumo do projeto 1**

| # | Severidade | Problema | Arquivo principal |
|---|---|---|---|
| 1 | CRITICAL | SQL Injection por concatenação de string (+ `/admin/query` aberto, senha em texto puro, `SECRET_KEY` exposta no `/health`) | `models.py`, `app.py`, `controllers.py` |
| 2 | MEDIUM | Query N+1 em dois níveis na listagem de pedidos, sem paginação nem índices | `models.py` |
| 3 | MEDIUM | Validação duplicada (e já divergente) entre `criar`/`atualizar` + serialização repetida 3× | `controllers.py`, `models.py` |
| 4 | LOW | Magic numbers nas faixas de desconto | `models.py` |
| 5 | LOW | `print()` como log, concatenação manual de strings, dado sensível em log | `controllers.py`, `app.py` |

---

### Projeto 2 — `ecommerce-api-legacy/` (Node.js/Express — LMS API com checkout)

**Estrutura atual:** 3 arquivos em `src/` — `app.js` (14 linhas, só sobe o servidor), `AppManager.js` (141 linhas, a aplicação inteira) e `utils.js` (25 linhas, configuração + cache global + "criptografia"). Não existe camada de model, controller ou service: o `AppManager` é ao mesmo tempo o roteador, o repositório e a regra de negócio.

---

#### 1. [CRITICAL] God Class `AppManager` com credenciais hardcoded e dados de cartão em log

**Onde:**
- `AppManager.js:1-141` — a classe inteira.
- `utils.js:1-7` — objeto `config` com `dbPass: "senha_super_secreta_prod_123"` e `paymentGatewayKey: "pk_live_1234567890abcdef"`.
- `AppManager.js:45` — `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`.

**Por que é relevante:** são duas falhas que se reforçam. A primeira é estrutural: `AppManager` cria a conexão com o banco no construtor (`AppManager.js:7`), define o schema e o seed (`initDb`, linhas 10-23), registra as rotas HTTP (`setupRoutes`, linha 25), e ainda implementa a "autorização" do pagamento (linha 46). É a definição literal de God Class — não há como testar a regra de checkout sem subir um SQLite e um Express junto, porque a regra só existe dentro do callback da rota. Também não há injeção de dependência: o banco é instanciado com `new sqlite3.Database` dentro do próprio construtor, então trocar SQLite por Postgres significa reescrever o arquivo todo.

A segunda é de segurança e é pior: as credenciais de produção estão versionadas em texto puro no repositório (o prefixo `pk_live_` indica chave de gateway real, não sandbox), e o `console.log` da linha 45 imprime **o número do cartão do cliente junto com a chave do gateway** em toda transação. Qualquer coletor de log — arquivo, Docker, CloudWatch — passa a armazenar dado de cartão em claro, o que quebra PCI-DSS diretamente. Em PHP é o mesmo erro de deixar a senha do banco no `config.php` commitado e dar `error_log($_POST)` no checkout.

**Agravantes na mesma família:**
- `utils.js:17-23` — `badCrypto` não é hash: concatena o **base64** da senha 10.000 vezes e devolve os 10 primeiros caracteres. Base64 é reversível, e o corte em 10 chars significa que só os 5 primeiros caracteres da senha influenciam o resultado — colisão trivial. Além disso, o loop de 10.000 iterações é puro desperdício de CPU, síncrono, bloqueando o event loop.
- `AppManager.js:68` — se o cliente não mandar senha, o sistema cria a conta com a senha default `"123456"` silenciosamente, sem avisar ninguém.
- `AppManager.js:18` — seed grava a senha `'123'` em texto puro, sem passar nem pelo `badCrypto`.
- `AppManager.js:46` — o "gateway de pagamento" é `cc.startsWith("4") ? "PAID" : "DENIED"`, ou seja, qualquer cartão começando com 4 é aprovado. Regra de integração externa hardcoded dentro do controller, sem abstração de gateway.
- `utils.js:9-10` — `globalCache` e `totalRevenue` são estado global mutável exportado do módulo; o cache cresce indefinidamente (`logAndCache`, linha 12-15) sem TTL nem limite de tamanho.

**Correção esperada:** quebrar o `AppManager` em camadas (routes → controllers → services → repositories), injetar a conexão de banco em vez de instanciá-la; mover toda a `config` para variáveis de ambiente e remover o arquivo do histórico; nunca logar PAN de cartão; substituir `badCrypto` por `bcrypt`/`argon2`; extrair o gateway de pagamento para uma interface com implementação real e fake.

---

#### 2. [MEDIUM] Query N+1 em dois níveis no relatório financeiro, com contadores manuais de concorrência

**Onde:** `AppManager.js:80-129` (`GET /api/admin/financial-report`).

**Por que é relevante:** o endpoint faz `SELECT * FROM courses` e, para cada curso, dispara um `SELECT` de matrículas (linha 92); para cada matrícula, dispara **mais dois** `SELECT` — um de usuário (linha 104) e um de pagamento (linha 106). Com 20 cursos e 30 matrículas por curso são `1 + 20 + (600 × 2) = 1.221` queries para montar um relatório que um único `SELECT` com três `JOIN` (`courses` → `enrollments` → `users` + `payments`) resolveria. Não há `LIMIT`, paginação nem filtro de período: o relatório sempre varre a base inteira e piora linearmente com o crescimento.

Pior que o N+1 é o controle de fluxo. Como o `sqlite3` é assíncrono por callback, o autor teve que inventar dois contadores manuais (`coursesPending`, linha 86, e `enrPending`, linha 93) para saber quando responder. Isso gera três defeitos concretos:
- **Race condition na ordem:** `report.push(courseData)` (linhas 96 e 119) executa na ordem de conclusão das queries, não na ordem dos cursos — o mesmo request devolve o relatório em ordens diferentes a cada chamada.
- **Erros ignorados:** os callbacks das linhas 104 e 106 recebem `err` e nunca o checam; um erro de banco vira `user = undefined` e o relatório mostra `'Unknown'` como se fosse um dado válido.
- **Crash em produção:** na linha 93, se a query de matrículas falhar, `enrollments` vem `undefined` e `enrollments.length` lança `TypeError` dentro de um callback assíncrono — sem `try/catch` possível, o processo Node inteiro cai.

**Correção esperada:** substituir os três níveis de callback por uma query agregada com `JOIN` (`SUM` do faturamento no próprio SQL), migrar para a API com `Promise`/`async-await` eliminando os contadores manuais, tratar todos os `err` e adicionar paginação.

---

#### 3. [MEDIUM] Checkout sem transação e banco sem integridade referencial

**Onde:**
- `AppManager.js:50-63` — a sequência de `INSERT` do checkout.
- `AppManager.js:12-16` — `CREATE TABLE` sem nenhuma `FOREIGN KEY`.
- `AppManager.js:131-137` — `DELETE /api/users/:id`.

**Por que é relevante:** o checkout faz quatro escritas encadeadas (usuário → matrícula → pagamento → auditoria) sem `BEGIN TRANSACTION`/`COMMIT`. Se o `INSERT` de pagamento falhar (linha 55), a matrícula da linha 50 **já foi gravada e permanece** — o aluno fica matriculado num curso que nunca pagou, e o sistema devolve 500 como se nada tivesse acontecido. É o caso clássico em que ou tudo é commitado ou nada é. Vale notar que o erro do `INSERT` de auditoria (linha 57) sequer é verificado: o callback recebe `err` e responde `200 Sucesso` de qualquer forma.

Do lado do schema, nenhuma das quatro tabelas declara `FOREIGN KEY` (linhas 12-16) — e o SQLite ainda exige `PRAGMA foreign_keys = ON` para aplicá-las. O resultado está confessado no próprio código: o `DELETE /api/users/:id` responde *"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco"* (linha 135). Ou seja, o endpoint gera órfãos por design, ignora o `err` do callback e responde sucesso mesmo quando o `id` não existe.

Some-se a validação de entrada: a linha 35 checa apenas presença dos campos, sem validar formato de e-mail, tipo ou formato do cartão. Se `card` vier como número em vez de string, `cc.startsWith` (linha 46) lança `TypeError` e derruba o processo. Não existe middleware de validação nem `error handler` registrado no Express (`app.js:1-14`).

**Correção esperada:** envolver o checkout em transação com rollback, declarar as `FOREIGN KEY` (com `ON DELETE` explícito) e habilitar o `PRAGMA`, checar todos os `err`, adicionar middleware de validação de payload e um `error handler` central no Express.

---

#### 4. [LOW] Nomenclatura de variáveis e do contrato da API

**Onde:** `AppManager.js:29-33` e o corpo esperado do `POST /api/checkout`.

```js
let u = req.body.usr;
let e = req.body.eml;
let p = req.body.pwd;
let cid = req.body.c_id;
let cc = req.body.card;
```

**Por que é relevante:** cinco variáveis de uma letra numa função de 50 linhas — ao chegar na linha 68 (`badCrypto(p || "123456")`) já não é óbvio que `p` é a senha. O `e` é especialmente ruim porque é a convenção universal de `error`/`event` em JavaScript, o que induz a erro em qualquer manutenção futura. E o problema vaza para fora do código: `usr`, `eml`, `pwd` e `c_id` são o **contrato público da API**, abreviações inconsistentes (`c_id` com underscore, `eml` sem) que qualquer consumidor precisa adivinhar.

No mesmo bloco: tudo é declarado com `let` mesmo nunca sendo reatribuído (deveria ser `const`), e a linha 26 guarda `const self = this` no estilo pré-ES6 — necessário apenas porque os callbacks das linhas 50 e 54 usam `function(err)` para acessar `this.lastID`, misturando dois estilos de `this` no mesmo arquivo (`this.db` nas linhas 37/40, `self.db` nas 54/57).

**Correção esperada:** nomes completos (`userName`, `email`, `password`, `courseId`, `cardNumber`), padronizar o payload da API em `camelCase` descritivo, `const` por padrão e eliminar o `self` extraindo a lógica para métodos/serviços nomeados.

---

#### 5. [LOW] `console.log` como log, código morto e export por valor de estado mutável

**Onde:** `utils.js:9-10`, `utils.js:25`, `utils.js:12-15`, `AppManager.js:45`, `app.js:13`.

**Por que é relevante:** três detalhes pequenos que juntos indicam código nunca revisado.
- `totalRevenue` (`utils.js:10`) é um número exportado na linha 25. Em CommonJS, exportar um primitivo exporta uma **cópia do valor** — qualquer `totalRevenue += x` dentro de `utils.js` jamais seria visto por quem importou. O `AppManager.js:2` chega a importá-lo e nunca o usa; é uma armadilha esperando alguém "consertar" o acumulador e não entender por que o valor fica sempre em zero. `globalCache` também é exportado (linha 25) e nunca lido em lugar nenhum: o cache é escrito por `logAndCache` e ninguém consome.
- `logAndCache` (`utils.js:12-15`) faz duas coisas sem relação — loga e escreve em cache — e o nome com "and" denuncia isso.
- `console.log` é o único mecanismo de log do projeto (`utils.js:13`, `AppManager.js:45`, `app.js:13`), sem nível, timestamp ou destino configurável. Não há como separar erro de informação, nem desligar o log de cartão em produção.

**Correção esperada:** remover o estado global e o código morto, separar cache de log em módulos próprios (cache com TTL, se realmente necessário) e adotar um logger estruturado (`pino`/`winston`) com níveis.

---

**Resumo do projeto 2**

| # | Severidade | Problema | Arquivo principal |
|---|---|---|---|
| 1 | CRITICAL | God Class `AppManager` (banco + rotas + negócio + pagamento) com credenciais hardcoded, cartão em log e hash falso | `AppManager.js`, `utils.js` |
| 2 | MEDIUM | Query N+1 em dois níveis no relatório financeiro, com contadores manuais, race condition e erros ignorados | `AppManager.js` |
| 3 | MEDIUM | Checkout sem transação, schema sem `FOREIGN KEY` e `DELETE` que gera órfãos | `AppManager.js` |
| 4 | LOW | Variáveis de uma letra e abreviações inconsistentes no contrato da API (`usr`, `eml`, `c_id`) | `AppManager.js` |
| 5 | LOW | `console.log` como log, código morto e export por valor de estado mutável | `utils.js` |

---

### Projeto 3 — `task-manager-api/` (Python/Flask — API de Task Manager)

**Estrutura atual:** 17 arquivos distribuídos em `models/`, `routes/`, `services/` e `utils/`, com SQLAlchemy no lugar de SQL cru. É de longe o projeto mais organizado dos três — mas a separação é só de pastas: não existe camada de controller/service, então a regra de negócio mora dentro dos handlers HTTP dos blueprints, e as pastas `services/` e `utils/` estão praticamente mortas.

---

#### 1. [CRITICAL] Autenticação quebrada — MD5 sem salt, hash de senha devolvido no JSON e token falso

**Onde:**
- `models/user.py:29` — `self.password = hashlib.md5(pwd.encode()).hexdigest()`
- `models/user.py:32` — `check_password` comparando o MD5 diretamente
- `models/user.py:21` — `'password': self.password` dentro do `to_dict()`
- `routes/user_routes.py:210` — `'token': 'fake-jwt-token-' + str(user.id)`
- `app.py:13` — `SECRET_KEY = 'super-secret-key-123'`
- `services/notification_service.py:7-10` — host, usuário e senha do SMTP hardcoded

**Por que é relevante:** o `to_dict()` do `User` inclui o campo `password`, e esse mesmo `to_dict()` é a resposta de `GET /users/<id>` (`user_routes.py:33`), de `POST /users` (`:85`), de `PUT /users/<id>` (`:129`) e do próprio `POST /login` (`:209`). Ou seja, **qualquer pessoa que consulte um usuário recebe o hash da senha dele no JSON** — sem autenticação nenhuma, já que não há middleware de auth em lugar algum. E o hash é MD5 puro, sem salt: os hashes do seed (`seed.py:19,26,33` — senhas `1234`, `abcd`, `pass`) são quebrados por rainbow table em segundos. Duas senhas iguais geram o mesmo hash, então dá para inferir quem compartilha senha só olhando o JSON.

O `/login` fecha o ciclo: devolve `'fake-jwt-token-' + user.id`, um token **previsível, sem assinatura e sem expiração**. Como nenhuma rota valida token, ele é decorativo — mas dá a falsa impressão de que existe autenticação. Na prática, `DELETE /users/1` e `PUT /users/1` (que permite mudar o próprio `role` para `admin`, `:119-122`) estão abertos para qualquer um. O método `is_admin()` (`models/user.py:34`) existe e nunca é chamado em nenhum lugar do projeto — não há uma única verificação de autorização.

**Agravantes na mesma família:**
- `app.py:13` — `SECRET_KEY` fixa no código; `app.py:34` — `debug=True` com `host='0.0.0.0'`, o que expõe o console interativo do Werkzeug na rede.
- `app.py:15` — `CORS(app)` sem restrição de origem: qualquer site pode chamar a API a partir do navegador da vítima.
- `services/notification_service.py:10` — `email_password = 'senha123'` versionada, no mesmo padrão do `config.php` commitado.
- `user_routes.py:64` — senha mínima de 4 caracteres.
- `user_routes.py:198-202` — o login responde 401 antes de checar a senha quando o e-mail não existe, permitindo enumerar contas válidas pelo tempo/ordem de resposta.

**Correção esperada:** trocar MD5 por `bcrypt`/`argon2` com salt, remover `password` de qualquer serialização de saída (schema de resposta separado do model), emitir JWT assinado de verdade com expiração, adicionar middleware de autenticação/autorização nas rotas de escrita e mover `SECRET_KEY`, credenciais de SMTP e origens de CORS para variáveis de ambiente.

---

#### 2. [MEDIUM] Query N+1 na listagem de tasks e nos relatórios

**Onde:**
- `routes/task_routes.py:14` + `:42` + `:51` — `GET /tasks`
- `routes/report_routes.py:53-56` — `GET /reports/summary`
- `routes/report_routes.py:159-163` — `GET /categories`
- `routes/user_routes.py:22` — `GET /users`

**Por que é relevante:** o `GET /tasks` carrega todas as tasks e, dentro do loop, dispara `User.query.get(t.user_id)` (linha 42) e `Category.query.get(t.category_id)` (linha 51) para cada uma — `1 + 2N` queries para montar uma lista que um `joinedload` (ou um `JOIN`) resolveria em uma. Pior: os relacionamentos `task.user` e `task.category` **já estão declarados** em `models/task.py:20-21` e simplesmente não são usados; o código refaz à mão o que o ORM entregaria.

O mesmo padrão se repete em três outros endpoints: o `/reports/summary` percorre todos os usuários e faz um `filter_by(user_id=...).all()` por usuário (linha 56) só para contar quantas estão concluídas — contagem que o banco faria com um `GROUP BY`; o `/categories` faz um `COUNT` por categoria dentro do loop (linha 163); e o `/users` acessa `len(u.tasks)` (linha 22), que dispara um `SELECT` lazy por usuário.

Some-se a isso que **nenhum endpoint de listagem tem paginação ou `LIMIT`** (`/tasks`, `/users`, `/tasks/search`, `/reports/summary`): a resposta cresce junto com a tabela, sem teto. E há desperdício adicional em cima disso — o `/reports/summary` dispara 12 `COUNT` separados (linhas 15-28) onde dois `GROUP BY` bastariam, e depois ainda carrega **todas** as tasks em memória (linha 30) para contar as atrasadas em Python, algo que um `WHERE due_date < now()` faria no banco (mesmo padrão em `task_routes.py:281`).

**Correção esperada:** usar `joinedload`/`selectinload` nos relacionamentos já declarados, trocar os loops de contagem por agregações `GROUP BY` no banco, filtrar as atrasadas via `WHERE` em vez de em memória e introduzir paginação em todas as listagens.

---

#### 3. [MEDIUM] Regra de negócio duplicada nos handlers — e as camadas `models`/`utils` existem mas não são usadas

**Onde:**
- Cálculo de "atrasada" copiado 6 vezes: `task_routes.py:30-39`, `task_routes.py:71-80`, `task_routes.py:283-287`, `user_routes.py:171-180`, `report_routes.py:34-43`, `report_routes.py:132-135` — enquanto `Task.is_overdue()` (`models/task.py:50-59`) faz exatamente isso e **nunca é chamado**.
- Serialização manual da task refeita em `task_routes.py:17-28` e `user_routes.py:162-169`, apesar de `Task.to_dict()` (`models/task.py:23-36`) existir.
- Validação de status/prioridade duplicada entre `create_task` (`task_routes.py:110-114`) e `update_task` (`task_routes.py:177-183`); os métodos `Task.validate_status()` e `Task.validate_priority()` (`models/task.py:38-48`) nunca são chamados.
- `utils/helpers.py:57-108` — `process_task_data()`, uma **terceira** implementação completa da mesma validação, importada por ninguém.
- Validação de e-mail com o mesmo regex copiado em `user_routes.py:61` e `:106`, enquanto `helpers.validate_email()` (`utils/helpers.py:19-23`) existe e não é usada.

**Por que é relevante:** a mesma regra vive em até seis lugares, e as versões já divergem entre si — o `/tasks` e o `/users/<id>/tasks` devolvem o campo `overdue`, mas o `GET /tasks/search` (`task_routes.py:266-269`) usa `to_dict()` e **não devolve** `overdue` nenhum; o `to_dict()` do model, por sua vez, transforma `tags` em lista, enquanto o dict manual do `/tasks` faz o mesmo `split` copiado à mão (linha 28). Qualquer mudança na definição de "atrasada" — considerar fuso horário, incluir o status `blocked` — exige encontrar as seis cópias.

Isso denuncia o problema arquitetural de fundo: **não existe camada de controller nem de service**. Os blueprints em `routes/` são simultaneamente roteamento, validação, regra de negócio e serialização; o `models/` guarda métodos de domínio que ninguém invoca; o `utils/helpers.py` é código morto quase inteiro (`format_date`, `calculate_percentage`, `sanitize_string`, `generate_id`, `log_action`, `is_valid_color`, `parse_date`, `process_task_data` — importados só parcialmente em `report_routes.py:7` e nunca chamados); e `services/notification_service.py` **não é importado por arquivo nenhum**, ou seja, a API nunca notifica ninguém apesar de ter um serviço de notificação pronto. A pasta sugere uma arquitetura que o código não pratica.

**Correção esperada:** extrair controllers/services por domínio, deixar as rotas apenas com roteamento e serialização de resposta, centralizar a regra de "atrasada" em `Task.is_overdue()` (usado por todos), unificar a validação em um schema único reaproveitado por `POST` e `PUT`, e ou ligar o `NotificationService` ao fluxo de atribuição de task ou removê-lo.

---

#### 4. [LOW] Magic numbers espalhados — com as constantes já definidas e ignoradas

**Onde:** `utils/helpers.py:110-116` define exatamente as constantes que faltam, e nenhuma é importada:

```python
VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
VALID_ROLES = ['user', 'admin', 'manager']
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'
```

Enquanto isso, os literais aparecem soltos em: `task_routes.py:96,99` e `:167,169` (o `3` e o `200` do título), `task_routes.py:104,113` e `:182` (o `3` default e a faixa `1..5` de prioridade), `task_routes.py:110` e `:177` (a lista de status literal, duas vezes), `user_routes.py:64` e `:115` (o `4` da senha), `user_routes.py:71` e `:120` (a lista de roles literal, duas vezes), `report_routes.py:45` (`timedelta(days=7)`), `report_routes.py:129` (`if t.priority <= 2` definindo "alta prioridade" sem nome).

**Por que é relevante:** o caso mais claro é `report_routes.py:83-89`, onde o relatório mapeia prioridade para `critical/high/medium/low/minimal` — a semântica dos números 1 a 5 existe, está documentada nesse dicionário, e em nenhum outro lugar do código. O `if t.priority <= 2` da linha 129 depende desse significado implícito: ninguém que leia só aquela linha sabe por que `2` é o corte. E como as regras estão duplicadas entre `POST` e `PUT` (problema 3), cada magic number tem duas cópias que podem divergir — mudar o limite do título para 300 exige lembrar de quatro lugares.

**Correção esperada:** importar e usar as constantes que já existem (ou movê-las para um módulo de configuração/domínio), transformar status, role e prioridade em `Enum`, e nomear o corte de "alta prioridade".

---

#### 5. [LOW] `print()` como log, `except:` nu engolindo erros e imports não usados

**Onde:**
- `print()` como log: `task_routes.py:149`, `:219`, `:234`; `user_routes.py:83`, `:89`, `:147`; `services/notification_service.py:21,24`; `seed.py:93-96`. Existe um `helpers.log_action()` (`utils/helpers.py:36-41`) — que também é `print` — e nunca é chamado.
- `except:` nu: `task_routes.py:62`, `:137`, `:204`, `:236`; `user_routes.py:130`, `:149`; `report_routes.py:186`, `:207`, `:221`; `utils/helpers.py:46,49,88`.
- Imports mortos: `app.py:7` (`os, sys, json`), `task_routes.py:7` (`json, os, sys, time`), `user_routes.py:6` (`hashlib, json`), `report_routes.py:8` (`json`), `utils/helpers.py:3-7` (`os, json, sys, math, hashlib`).

**Por que é relevante:** o `print` não tem nível, timestamp nem destino configurável — não dá para separar erro de informação nem desligar em produção. Mas o problema real é o `except:` nu: em `task_routes.py:62`, um `except:` envolve o handler inteiro do `GET /tasks` e devolve `{'error': 'Erro interno'}, 500` **sem registrar nada em lugar nenhum** — se a listagem quebrar, não existe stack trace, nem no log, nem na resposta. Um `except:` sem tipo também captura `KeyboardInterrupt` e `SystemExit`, o que atrapalha até o shutdown do processo. O mesmo padrão aparece em 11 lugares, e nos `try/except` de escrita (`report_routes.py:186,207,221`) o rollback acontece às cegas, sem distinguir violação de constraint de falha de conexão.

Na mesma linha de legibilidade: `is_overdue()` (`models/task.py:50-59`), `is_admin()` (`models/user.py:34-38`) e `validate_status()` (`models/task.py:38-43`) usam `if/else` aninhados para devolver `True`/`False` onde uma expressão booleana direta bastaria; `type(tags) == list` (`task_routes.py:141`, `:210`) deveria ser `isinstance`; e `datetime.utcnow()` está deprecado desde o Python 3.12 (usado em ~15 lugares), devendo ser `datetime.now(timezone.utc)`.

**Correção esperada:** substituir `print` pelo módulo `logging` com níveis, trocar todo `except:` por exceções específicas com log do stack trace, registrar um error handler central no Flask em vez de `try/except` por handler, remover os imports mortos e migrar `utcnow()` para a API com timezone.

---

**Resumo do projeto 3**

| # | Severidade | Problema | Arquivo principal |
|---|---|---|---|
| 1 | CRITICAL | MD5 sem salt, hash de senha devolvido no JSON, token falso, `SECRET_KEY` e SMTP hardcoded, zero autorização | `models/user.py`, `routes/user_routes.py`, `app.py` |
| 2 | MEDIUM | Query N+1 no `/tasks` e nos relatórios (relacionamentos declarados e não usados), sem paginação | `routes/task_routes.py`, `routes/report_routes.py` |
| 3 | MEDIUM | Regra de "atrasada" duplicada 6× e validação 3×, com `models`/`utils`/`services` existindo mas nunca chamados | `routes/*.py`, `utils/helpers.py` |
| 4 | LOW | Magic numbers de prioridade, título, senha e status — com as constantes já definidas e ignoradas | `utils/helpers.py`, `routes/task_routes.py` |
| 5 | LOW | `print()` como log, `except:` nu sem registro de erro, imports mortos e `utcnow()` deprecado | `routes/*.py`, `utils/helpers.py` |

---

## Construção da Skill

A skill vive em `.claude/skills/refactor-arch/` e é composta por um `SKILL.md` (o prompt que orquestra) e cinco arquivos de referência em `references/` (o conhecimento de domínio). A pasta é idêntica nos três projetos — é a mesma cópia, sem nenhum ajuste local.

```
.claude/skills/refactor-arch/
├── SKILL.md                              # orquestração das 3 fases + regras invioláveis
└── references/
    ├── project-analysis.md               # Fase 1 — heurísticas de detecção
    ├── antipattern-catalog.md            # Fase 2 — 19 anti-patterns com sinais de detecção
    ├── report-template.md                # Fase 2 — formato do relatório
    ├── architecture-guidelines.md        # Fase 3 — MVC alvo e estrutura por stack
    └── refactoring-playbook.md           # Fase 3 — 17 transformações antes/depois
```

### Decisões de design

**1. `SKILL.md` orquestra, os `references/` sabem.**
O `SKILL.md` tem 94 linhas e quase nenhum conhecimento técnico: ele diz *o que fazer, em que ordem e o que é proibido*. Todo o conteúdo — os greps de detecção, a tabela de severidades, os exemplos de código — está nos arquivos de referência, carregados **sob demanda, na fase correspondente**. Uma tabela no topo do `SKILL.md` diz qual arquivo ler em qual fase, com instrução explícita de não ler todos de uma vez. O motivo é prático: os cinco arquivos somam ~1.550 linhas, e carregar tudo de largada gastaria contexto com o playbook de refatoração antes mesmo de saber se o usuário vai aprovar a Fase 3.

**2. Cinco regras invioláveis no topo do `SKILL.md`.**
São restrições que, se violadas, invalidam a entrega inteira — por isso ficam antes da descrição das fases, não diluídas no meio dela:

| Regra | Por quê |
|---|---|
| Nenhuma escrita antes do `y` | O portão humano é requisito do desafio. Nas Fases 1 e 2 só são permitidas ferramentas de leitura — inclusive salvar o relatório em `reports/` só acontece depois da aprovação. |
| Todo finding tem arquivo e linha reais | É o item do checklist mais fácil de falhar por alucinação. A regra manda descartar o achado que não foi localizado fisicamente. |
| Nada de suposição de stack | Vale o manifesto e os imports, não o nome da pasta — ver o problema do `ecommerce-api-legacy` abaixo. |
| Comportamento preservado, menos onde preservá-lo é preservar a falha | A Fase 3 não pode mudar contrato de API — exceto por **correção de segurança, que é obrigatória e não opcional**: remover campo sensível da resposta, remover endpoint sem controle de acesso, **exigir autenticação em rota que hoje responde sem credencial**, endurecer validação insegura. Cada uma vai listada como *breaking change*. E a regra que fecha a brecha: **correção de segurança não fica atrás de flag desligada por default** — vale o comportamento com os defaults versionados, não o comportamento possível. |
| Contagens vêm de comando executado | `Files: 4 analyzed` e `Total: 14 findings` saem de `wc -l`/`find` e da soma conferida, não de estimativa. |

**3. Fase 2 com resposta ambígua = `n`.**
O `SKILL.md` manda tratar silêncio ou resposta não-inequívoca como recusa, oferecendo salvar apenas o relatório. É o comportamento seguro quando o próximo passo reescreve o projeto inteiro.

**4. A Fase 3 captura uma linha de base antes de tocar em qualquer arquivo.**
Antes da primeira escrita, a skill sobe a aplicação original e registra status e forma de resposta de cada endpoint. Sem esse registro, "os endpoints continuam respondendo" é uma afirmação não verificável — e o checklist do desafio pede exatamente essa verificação. A instrução é explícita: nunca declarar validação verde sem ter executado o boot e as chamadas.

**5. Migração em ordem de dependência, validando por grupo.**
A Fase 3 migra `config/` → `models/` → `services/` → `controllers/` → `routes/` → `middlewares/` → composition root, e o playbook fecha com uma ordem recomendada de aplicação dos 16 padrões (segredos primeiro, limpeza por último). Validar a cada grupo, e não só no fim, torna uma quebra atribuível ao passo que a causou.

### Quais anti-patterns entraram e por quê

O mínimo exigido era 8; o catálogo tem **19**, com severidade distribuída. A quantidade não é enfeite: cada um foi incluído porque corresponde a um achado real da análise manual acima, e a numeração (`AP-01`…`AP-19`) permite que o playbook referencie a correção sem repetir a explicação.

| ID | Severidade | Anti-pattern | Origem na análise manual |
|---|---|---|---|
| AP-01 | CRITICAL | SQL Injection por concatenação | Projeto 1, achado 1 (~15 ocorrências em `models.py`) |
| AP-02 | CRITICAL | Credenciais e segredos hardcoded | Projetos 1, 2 e 3 — `SECRET_KEY`, `pk_live_*`, SMTP |
| AP-03 | CRITICAL | God Class / God Module | Projeto 2, achado 1 (`AppManager.js`) |
| AP-04 | CRITICAL | Autenticação quebrada, ausente ou desligada | Projeto 3, achado 1 (MD5 sem salt); `badCrypto` do projeto 2; **ausência total de guard** nos três (0 rotas exigiam credencial) |
| AP-05 | CRITICAL | Exposição de dado sensível | Senha no JSON (proj. 3), cartão em log (proj. 2), `/admin/query` (proj. 1) |
| AP-06 | HIGH | Regra de negócio dentro do handler | Projeto 3, achado 3 — a violação central de MVC |
| AP-07 | HIGH | Acoplamento forte, sem injeção de dependência | Projeto 2 — `new sqlite3.Database` no construtor |
| AP-08 | HIGH | Estado global mutável | Projeto 2 — `globalCache`, `totalRevenue` |
| AP-09 | HIGH | Escrita multi-passo sem transação | Projeto 2, achado 3 — checkout com 4 `INSERT` |
| AP-10 | HIGH | Erro engolido, ignorado ou espalhado | Projeto 3 — `except:` nu em 11 lugares; `err` ignorado no proj. 2 |
| AP-11 | MEDIUM | Query N+1 | Achado presente nos **três** projetos |
| AP-12 | MEDIUM | Listagem sem paginação | Três projetos — nenhum endpoint tem `LIMIT` |
| AP-13 | MEDIUM | Duplicação de regra e validação | Projetos 1 e 3 — regra de "atrasada" copiada 6× |
| AP-14 | MEDIUM | Validação ausente ou superficial na rota | Projeto 2 — só checagem de presença |
| AP-15 | MEDIUM | **APIs deprecated** (checagem obrigatória) | Projeto 3 — `utcnow()`, `Model.query.get()` |
| AP-16 | LOW | Magic numbers | Projetos 1 e 3 — faixas de desconto, `priority <= 2` |
| AP-17 | LOW | `print`/`console.log` como log | Três projetos |
| AP-18 | LOW | Nomenclatura ruim | Projeto 2 — `u`, `e`, `p`, `usr`, `eml`, `c_id` |
| AP-19 | LOW | Código e camadas mortas | Projeto 3 — `services/` que ninguém importa |

Três escolhas dentro do catálogo merecem justificativa:

- **AP-15 é a única checagem marcada como obrigatória.** O desafio exige detecção de APIs deprecated, e é o tipo de coisa que um auditor pula quando não encontra nada. A regra é que a linha `Deprecated APIs:` apareça no relatório **sempre**, inclusive como `nenhuma ocorrência encontrada` — assim o item do checklist é auditável nos dois casos. A tabela cobre 17 APIs de Python, Flask, SQLAlchemy 2.0, Node, Express 5, Sequelize e JavaScript.
- **Regras de promoção de severidade, em vez de severidade fixa por ID.** Um `console.log` é AP-17 (LOW); um `console.log` imprimindo número de cartão é AP-05 (CRITICAL). O catálogo tem uma regra explícita: exposição de dado sensível sobe para CRITICAL, e um achado sobe de nível se tornar o código impossível de testar em isolamento. Sem isso, o `AppManager.js:45` do projeto 2 seria classificado como um problema de legibilidade.
- **Agrupamento por raiz.** Quinze `print()` viram **um** finding com sub-itens. A regra existe porque a alternativa — inflar a contagem com ocorrências repetidas — atinge o mínimo de 5 findings sem auditar nada.

- **AP-04 cobre três estados diferentes, e o terceiro só entrou na segunda devolutiva.** Hash fraco é o caso óbvio; guard atrás de flag desligada foi a primeira devolutiva; **ausência total de controle de acesso** foi a segunda. Este último é o mais fácil de subnotificar, porque não existe padrão suspeito para o grep encontrar — a detecção é por **contagem**: rotas registradas contra rotas com guard. Por isso a correção virou uma transformação própria, **RP-17**, separada do RP-04: hash forte protege a senha guardada e não fecha rota nenhuma.

O `AP-19` (código morto) e o `AP-06` (regra no handler) são os que justificam a existência do terceiro projeto: são os únicos que aparecem em codebases já organizadas por pasta.

### Como a skill ficou agnóstica de tecnologia

Cinco mecanismos concretos, não só a intenção:

**a) Detecção por precedência, não por convenção de nome.**
A regra é *manifesto de dependências > imports no código > extensão de arquivo*. O `project-analysis.md` traz uma tabela de 9 manifestos (`requirements.txt`, `package.json`, `composer.json`, `go.mod`, `pom.xml`, `Gemfile`, `Cargo.toml`, `*.csproj`, `pyproject.toml`) e exige que o framework seja **confirmado por import** — o manifesto dá a versão, o código prova o uso.

**b) Anti-patterns definidos por conceito, com sinais traduzíveis.**
Cada AP é descrito de forma independente de linguagem, e os greps são exemplos em Python e JavaScript porque são as stacks dos alvos. O catálogo diz explicitamente: *"traduza o sinal para a stack detectada — o equivalente de `print()` em PHP é `echo`/`var_dump`, em Go é `fmt.Println`"*. O que é detectado é "log sem nível nem destino configurável", não `print(`.

**c) Estrutura de diretórios por stack, com instrução de seguir a convenção do framework.**
O `architecture-guidelines.md` define os *papéis* das camadas de forma abstrata (com a regra da seta única e uma lista de "o que esta camada NUNCA faz") e depois dá a árvore concreta para Flask e para Express, mais o mapeamento para Laravel, Spring e Django. A instrução é literal: *"não force nomes Flask em um projeto Express"*.

**d) Playbook com o mesmo padrão nas duas linguagens.**
Os 16 padrões mostram antes/depois em Python **e** JavaScript sempre que a diferença importa — RP-08 (N+1), por exemplo, traz a versão SQL cru com `JOIN`, a versão ORM com `joinedload`, a agregação com `GROUP BY` e a conversão do inferno de callbacks do Node para uma query única. O texto abre dizendo que os exemplos são ilustrativos e o que se aplica é o padrão.

**e) Zero acoplamento textual aos projetos-alvo.**
Nenhum arquivo de referência cita `models.py`, `AppManager.js` ou `task_routes.py`. Os sinais foram *calibrados* contra os problemas reais encontrados na análise manual, mas escritos de forma genérica — é o que permite copiar a pasta entre os três projetos sem editar uma linha (e o `diff -r` entre as três cópias é vazio).

**f) Adaptação quando não há framework web.**
O `project-analysis.md` prevê o caso: se nenhum framework for detectado, a Fase 1 registra `Framework: nenhum (script/CLI)` e a Fase 3 adapta o MVC alvo — a camada View passa a ser a interface de entrada (CLI, worker, consumer).

### Desafios encontrados

**1. O projeto "organizado" é o mais difícil de auditar.**
O `task-manager-api` já tem `models/`, `routes/`, `services/` e `utils/` — e é justamente onde uma auditoria rasa conclui "está tudo certo" e devolve menos de 5 findings, furando o critério de aceite. A separação ali é só de pastas: a regra de negócio mora no handler, `Task.is_overdue()` existe e nunca é chamado, e `services/notification_service.py` não é importado por arquivo nenhum. A solução foi dupla: o catálogo termina com um checklist de varredura que avisa que projetos organizados concentram os achados em **AP-06, AP-10, AP-11, AP-13 e AP-19**, e o `SKILL.md` instrui, no passo 2 da Fase 2, a não pular categorias porque o projeto "parece organizado". O `project-analysis.md` ainda dá o grep que prova camada morta: um módulo em `services/` que nenhum arquivo importa.

**2. Distinguir anti-pattern de falso-positivo.**
`execute("SELECT ... WHERE id = ?", (id,))` e `execute("SELECT ... WHERE id = " + str(id))` são graficamente parecidos e completamente diferentes. Cada anti-pattern propenso a isso ganhou uma seção de falso-positivo — em AP-01, a regra é que o que importa é o valor entrar pelo parâmetro, não pela string. O caso mais sutil é o `ORDER BY` dinâmico, que **não pode** ser parametrizado: o RP-01 mostra a correção por allowlist, para a skill não "consertar" com um placeholder que quebraria a query.

**3. Nome de pasta mentindo sobre o domínio.**
O diretório se chama `ecommerce-api-legacy` e o projeto é um LMS (cursos, matrículas, pagamentos). Se a Fase 1 inferir domínio pelo nome da pasta, todo o resto da auditoria herda o erro. Daí a regra 3 do `SKILL.md` e a instrução de cruzar três evidências — rotas, tabelas e `api.http`/README — com um aviso explícito sobre nomes enganosos.

**4. Refatorar sem quebrar o contrato da API.**
Vários anti-patterns só se corrigem mudando a interface pública: `usr`/`eml`/`c_id` são nomes ruins **e** são o payload que o consumidor envia; introduzir paginação muda uma resposta que hoje é um array puro. A skill separa os dois casos. Mudança de nomenclatura em payload público: aceitar os dois nomes por um período (`req.body.userName ?? req.body.usr`). Paginação: se o contrato original devolvia array, manter o array e enviar os metadados em headers (`X-Total-Count`). E as correções de segurança que **precisam** quebrar — remover o campo `senha` da resposta, remover o `POST /admin/query`, exigir autenticação onde hoje não há — não são apenas permitidas: são obrigatórias, e obrigadas a aparecer numa seção de *breaking changes* no fim da Fase 3. Foi exatamente aqui que a primeira entrega errou; ver o desafio 7.

**5. Impedir validação declarada sem execução.**
"✓ Application boots without errors" é uma linha barata de imprimir. A contramedida ficou em três pontos: a linha de base capturada antes da refatoração, a exigência de colar a **saída real** do boot e das chamadas no relatório (não parafrasear), e uma lista de "erros que invalidam o relatório" no `report-template.md`, onde consta marcar validação como ✅ sem ter executado boot e chamadas.

**6. Contagem inflada como atalho para o critério de aceite.**
Os critérios pedem ≥ 5 findings, o que cria um incentivo ruim: reportar cinco ocorrências do mesmo `print()`. Além da regra de agrupamento por raiz, o passo 8 da Fase 2 diz o que fazer quando o resultado ficou abaixo do mínimo — *não inventar achados*, e sim revisar as categorias marcadas como ausentes, porque uma varredura rasa é a causa muito mais provável que um projeto limpo.

**7. A regra de preservar comportamento virou desculpa para não corrigir segurança.**
Este foi um erro real da primeira entrega, apontado na devolutiva do instrutor, e é o desafio mais instrutivo dos sete — porque a skill funcionou como escrita, e o que estava errado era a regra.

A redação original da regra 4 dizia que a Fase 3 não muda contrato, "com as únicas exceções permitidas" sendo correções de segurança. Duas palavras fizeram o estrago: *exceção* e *permitida*. Diante do finding de autenticação quebrada no `task-manager-api`, a Fase 3 leu a regra como um convite a minimizar o dano — construiu hash scrypt, JWT assinado, middleware, verificação de papel, e então embrulhou tudo em `if settings.AUTH_REQUIRED:` com o default `false`. O relatório registrou o finding como parcialmente resolvido e anexou a matriz de autorização rodada com `AUTH_REQUIRED=true`, que passava 8/8.

Nos defaults versionados — que é o que qualquer um obtém ao clonar e rodar `python app.py` — o resultado era este:

```
$ curl -i -X DELETE http://127.0.0.1:5000/users/3      # sem header Authorization
HTTP/1.1 200 OK
{"message":"Usuário deletado com sucesso"}
```

O impacto descrito no próprio finding continuava valendo integralmente. Pior: agora havia um `@require_admin` na rota, o que faz a revisão seguinte presumir proteção e não testar a chamada. **Controle de segurança desligado por default é controle ausente com uma camada de disfarce.**

O erro tem uma assinatura reconhecível: a mesma entrega removeu o campo `password` da resposta sem hesitar — quebrando qualquer cliente que lesse aquele campo — e ninguém propôs um `RETURN_PASSWORD=true` para suavizar a transição. As duas correções são da mesma natureza; só uma foi tratada como negociável. O projeto 2 confirma que a inconsistência era da regra e não da stack: lá o `X-Admin-Api-Key` passou a ser exigido incondicionalmente, sem flag, e isso foi registrado como breaking change sem discussão.

A correção foi na skill, não no projeto — e só então o projeto foi reprocessado. O que mudou está detalhado em *Revisão pós-devolutiva*, mais abaixo.

---

## Resultados

As três execuções da skill estão registradas em `reports/audit-project-{1,2,3}.md`. Os números abaixo saem desses relatórios e da validação executada no repositório — nenhum é estimativa.

### Saída da Fase 1 nos três projetos

O bloco descritivo que a skill imprime antes de qualquer julgamento. Os números
saem de comando executado (`find`, `wc -l`, contagem de rotas), não de estimativa.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.12
Framework:     Flask 3.1.1
Dependencies:  flask-cors
Domain:        API de E-commerce (produtos, usuários, pedidos com itens, relatório de vendas)
Architecture:  Camadas nominais vazando — app.py/controllers.py/models.py/database.py,
               com regra de negócio no model e SQL no arquivo de rotas
Source files:  4 files analyzed | ~780 lines
DB tables:     produtos, usuarios, pedidos, itens_pedido
Auth:          0 de 19 rotas exigem credencial (login não emite token)
Entry point:   app.py (`python app.py`, debug=True, host 0.0.0.0)
================================

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js 24)
Framework:     Express 4 (^4.18.2, lock 4.22.1)
Dependencies:  sqlite3 ^5.1.6
Domain:        LMS com fluxo de checkout (usuários, cursos, matrículas, pagamentos, audit log)
Architecture:  God Class — AppManager (141 linhas) com conexão, DDL, seed, roteamento e regra
Source files:  3 files analyzed | ~180 lines
DB tables:     users, courses, enrollments, payments, audit_logs
Auth:          0 de 3 rotas exigem credencial (nenhum middleware de autenticação)
Entry point:   src/app.js (`npm start` → main: src/app.js)
================================

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.12.3
Framework:     Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.0.52)
Dependencies:  python-dotenv (declarado e nunca importado)
Domain:        Task Manager (tasks, usuários, categorias, relatórios de produtividade)
Architecture:  Camadas por pasta, sem controller/service — models/, routes/, services/, utils/
               existem, mas 100% da regra vive nos handlers HTTP
Source files:  14 files analyzed | ~1.158 lines (1 seed, 3 __init__)
DB tables:     users, tasks, categories
Auth:          0 de 22 rotas exigem credencial (login devolve 'fake-jwt-token-' + id, que
               nenhuma rota valida)
Entry point:   app.py (`python app.py`, debug=True, host 0.0.0.0)
================================
```

A linha `Auth` é medida na Fase 1 — contagem de rotas registradas contra contagem
de rotas com guard — e é o número que vira finding AP-04 na Fase 2 e RP-17 na
Fase 3. Nos três projetos ela começou em zero; hoje é 13/17, 2/3 e 18/22, com as
públicas declaradas e justificadas rota a rota nos relatórios.

### Resumo dos relatórios de auditoria

| # | Projeto | Stack detectada na Fase 1 | Arquivos | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `code-smells-project` | Python 3.12 + Flask 3.1.1 | 4 (780 linhas) | 5 | 5 | 4 | 4 | **18** |
| 2 | `ecommerce-api-legacy` | Node.js 24 + Express ^4.18.2 + sqlite3 | 3 (180 linhas) | 5 | 5 | 3 | 4 | **17** |
| 3 | `task-manager-api` | Python 3.12 + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 | 14 (1.158 linhas) | 4 | 3 | 6 | 4 | **17** |
| | | | | **14** | **13** | **13** | **12** | **52** |

Os três passam com folga o mínimo de 5 findings e o mínimo de 1 CRITICAL/HIGH exigidos nos critérios de aceite.

**O domínio foi lido do código, não do nome da pasta.** No projeto 2 a Fase 1 detectou *LMS com checkout de cursos* — as tabelas são `courses` e `enrollments`, a rota é `/api/checkout` de curso. O diretório se chama `ecommerce-api-legacy`, e o relatório registra explicitamente essa divergência.

**Padrão que se repete nos três.** Cinco anti-patterns apareceram em todos: God Class/Module (AP-03), segredos hardcoded (AP-02), regra de negócio no controller (AP-06), acoplamento sem injeção de dependência (AP-07) e ausência de tratamento central de erro (AP-10). É o núcleo do que a refatoração desfaz.

**Detecção de APIs deprecated (AP-15).** A checagem é obrigatória e aparece no relatório mesmo quando negativa:

| Projeto | Resultado |
|---|---|
| 1 e 2 | `0 ocorrências` — registrado explicitamente na seção *APIs deprecated* de cada relatório |
| 3 | **34 ocorrências em 3 famílias** — `datetime.utcnow()`, `Model.query.get()` e `type(x) == list` — reportadas como finding MEDIUM 13 e corrigidas na Fase 3 |

### Comparação antes/depois

**Projeto 1 — `code-smells-project`**

```
ANTES  (4 arquivos, 780 linhas)          DEPOIS (41 arquivos, 1.687 linhas)
app.py            88   rotas             app.py                  entry point
controllers.py   292   handlers          src/config/             settings + constantes
models.py        314   SQL + regra       src/models/             acesso a dados
database.py       86   conexão + seed    src/services/           regra de negócio
                                         src/controllers/        fluxo HTTP
                                         src/views/routes.py     roteamento + gate de acesso
                                         src/schemas/            validação
                                         src/middlewares/        auth, erro, paginação
                                         src/infrastructure/     db, logger, token
                                         src/domain/errors.py    exceções de domínio
```

**Projeto 2 — `ecommerce-api-legacy`**

```
ANTES  (3 arquivos, 180 linhas)          DEPOIS (29 arquivos, 1.024 linhas)
src/AppManager.js 141  God Class:        src/config/             env + constantes
                       conexão + DDL +   src/models/             6 repositories
                       seed + rotas +    src/services/           checkout, user, report
                       regra de negócio  src/controllers/        3 controllers
src/app.js        14   bootstrap         src/routes/index.js     roteamento
src/utils.js      25   segredos          src/schemas/            validação com zod
                                         src/middlewares/        auth, erro, paginação
                                         src/infrastructure/     db, migrations, gateway, hasher
                                         src/server.js           composition root
```

**Projeto 3 — `task-manager-api`**

Este entrou já dividido em pastas — `models/`, `routes/`, `services/`, `utils/`. A separação era nominal: 100% da regra de negócio vivia nos handlers HTTP e `services/` tinha um único arquivo.

```
ANTES  (14 arquivos, 1.158 linhas)       DEPOIS (35 arquivos com conteúdo, 2.388 linhas)
routes/task_routes.py    299             src/controllers/        5 controllers (só fluxo)
routes/report_routes.py  223             src/services/           5 services (regra)
routes/user_routes.py    211             src/repositories/       3 repositories (query)
utils/helpers.py         116             src/models/             entidades SQLAlchemy
models/task.py            60             src/views/routes.py     22 rotas mapeadas
services/…                48  (1 arq.)   src/schemas/            validação
                                         src/middlewares/        auth, erro, paginação
                                         src/infrastructure/     db, logger, clock, security
```

O código cresce em linhas porque validação, tratamento de erro e configuração passaram a existir de fato — antes eram ausentes ou copiados. O que encolhe é a concentração: o maior arquivo cai de **314 → 132** linhas no projeto 1, **141 → 89** no projeto 2 e **299 → 188** no projeto 3.

**Sinais de anti-pattern, medidos por varredura no código antes e depois:**

| Sinal | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| SQL montado por concatenação | 10 → **0** | — (já parametrizado) | — (ORM) |
| Segredos literais no código | 1 → **0** | 4 → **0** | 2 → **0** |
| `except:` nu | — | — | 12 → **0** |
| `print()` / `console.log()` como log | 19 → **0** | 3 → **0** | 15 → **0** |
| APIs deprecated (3 famílias, 34 ocorrências) | — | — | 34 → **0** |

> As três ocorrências que a varredura ainda encontra em `task-manager-api/src/` estão dentro de *docstrings* — `domain/errors.py:6`, `middlewares/error_handler.py:3` e `infrastructure/clock.py:4` citam o anti-pattern removido para documentar por que a camada existe. Em código executável a contagem é zero nos três projetos.

### Checklist de validação preenchido

**Fase 1 — Análise**

| Item | P1 | P2 | P3 |
|---|:--:|:--:|:--:|
| Linguagem detectada corretamente | ✅ Python | ✅ JavaScript | ✅ Python |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express ^4.18.2 | ✅ Flask 3.0.0 + SQLAlchemy |
| Domínio da aplicação descrito corretamente | ✅ E-commerce | ✅ LMS com checkout | ✅ Task Manager |
| Número de arquivos analisados condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 14 |

**Fase 2 — Auditoria**

| Item | P1 | P2 | P3 |
|---|:--:|:--:|:--:|
| Relatório segue o template de `references/report-template.md` | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Findings ordenados por severidade (CRITICAL → LOW) | ✅ | ✅ | ✅ |
| Mínimo de 5 findings identificados | ✅ 18 | ✅ 17 | ✅ 17 |
| Detecção de APIs deprecated incluída | ✅ 0, registrado | ✅ 0, registrado | ✅ 34 achados |
| Skill pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |

**Fase 3 — Refatoração**

| Item | P1 | P2 | P3 |
|---|:--:|:--:|:--:|
| Estrutura de diretórios segue padrão MVC | ✅ | ✅ | ✅ |
| Configuração extraída para módulo de config (sem hardcoded) | ✅ `src/config/` | ✅ `src/config/` | ✅ `src/config/` |
| Models criados para abstrair dados | ✅ 3 models | ✅ 6 repositories | ✅ 3 models + 3 repositories |
| Views/Routes separadas para roteamento | ✅ `views/routes.py` | ✅ `routes/index.js` | ✅ `views/routes.py` |
| Controllers concentram o fluxo da aplicação | ✅ 5 | ✅ 3 | ✅ 5 |
| Error handling centralizado | ✅ `middlewares/error_handler.py` | ✅ `middlewares/errorHandler.js` | ✅ `middlewares/error_handler.py` |
| Gate de autenticação aplicado nas rotas (RP-17) | ✅ `middlewares/auth.py` — 13/17 rotas | ✅ `middlewares/adminAuth.js` — 2/3 rotas | ✅ `middlewares/auth.py` — 18/22 rotas |
| Nenhuma rota sensível responde sem credencial | ✅ matriz 17/17 | ✅ matriz 3/3 | ✅ matriz 22/22 |
| Entry point claro | ✅ `app.py` | ✅ `src/server.js` | ✅ `app.py` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem corretamente | ✅ 25/25 (com credencial) | ✅ 5/5 | ✅ 26/26 (com credencial) |

**Critérios de aceite do desafio — 3/3 projetos**

| Critério | P1 | P2 | P3 |
|---|:--:|:--:|:--:|
| Fase 1 detecta a stack corretamente | ✅ | ✅ | ✅ |
| Fase 2 encontra ≥ 5 findings | ✅ 18 | ✅ 17 | ✅ 17 |
| Fase 2 inclui ≥ 1 CRITICAL ou HIGH | ✅ 10 | ✅ 10 | ✅ 7 |
| Fase 3 — aplicação funciona após a refatoração | ✅ | ✅ | ✅ |

### Logs das aplicações rodando após a refatoração

Saída real de boot + smoke test dos três projetos, executados em sequência a partir da raiz do repositório.

**Projeto 1 — `code-smells-project`** (`.venv/bin/python app.py`)

```
2026-09-01 22:39:13,670 INFO loja servidor iniciado em http://127.0.0.1:5000
 * Serving Flask app 'src.app'
 * Debug mode: off
2026-09-01 22:39:13,674 INFO werkzeug WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit

GET    /                                  200
GET    /health                            200
GET    /produtos            (sem token)   401
GET    /produtos            (com token)   200
GET    /produtos/busca?q=note (com token) 200
GET    /produtos/1          (com token)   200
GET    /usuarios            (sem token)   401
GET    /usuarios            (token admin) 200
GET    /pedidos             (token admin) 200
GET    /pedidos/usuario/1   (token admin) 200
GET    /relatorios/vendas   (sem token)   401
GET    /relatorios/vendas   (token admin) 200
POST   /login (senha errada)              401
```

`debug=off` e o log estruturado com nome de aplicação (`loja`) são o resultado direto da correção dos findings 3 (segredos/config) e 16 (`print` como log). O `401` no login é o comportamento correto — antes da refatoração, `' OR '1'='1` como senha devolvia o usuário admin. Os demais `401` são o gate de autenticação da segunda devolutiva: `GET /relatorios/vendas` sem token respondia `200` até esta rodada.

**Projeto 2 — `ecommerce-api-legacy`** (`npm start`)

```
{"time":"2026-08-23T00:15:10.244Z","level":"warn","msg":"variáveis sensíveis ausentes: usando valores de desenvolvimento (ver .env.example)","variables":["PAYMENT_GATEWAY_KEY","ADMIN_API_KEY"]}
{"time":"2026-08-23T00:15:10.246Z","level":"info","msg":"LMS API no ar","port":3000,"env":"development"}

POST   /api/checkout (legado)       200
POST   /api/checkout (recusado)     400
GET    /api/admin/financial-report  200
GET      idem, sem a chave          401
DELETE /api/users/1                 200
```

O `warn` de boot é intencional: sem `.env`, a aplicação usa valores de desenvolvimento e avisa. Em `NODE_ENV=production` a mesma ausência **derruba o boot** em vez de subir com segredo default. O checkout aceita o payload legado (`usr`, `eml`, `c_id`, `card`) — contrato preservado. O `401` sem `X-Admin-Api-Key` é o finding 5 corrigido: esses dois endpoints não tinham autenticação nenhuma.

**Projeto 3 — `task-manager-api`** (`.venv/bin/python app.py`)

```
2026-08-22 21:15:11,627 INFO     taskmanager aplicação montada env=development debug=False
 * Serving Flask app 'src.app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit

GET    /                            200
GET    /health                      200
GET    /tasks                       200
GET    /tasks/search?q=bug          200
GET    /tasks/stats                 200
GET    /tasks/1                     200
GET    /users                       200
GET    /users/1                     200
GET    /users/1/tasks               200
GET    /categories                  200
GET    /reports/summary             200
GET    /reports/user/1              200
POST   /tasks                       201
DELETE /tasks/12 (limpeza)          200
```

As 22 rotas originais continuam registradas e respondendo. `debug=False` corrige o `app.run(debug=True, host='0.0.0.0')` do finding 3, que expunha o console interativo do Werkzeug na rede.

### Breaking changes assumidos

A refatoração preservou o contrato de API — mesmas rotas, mesmos métodos, mesma forma de resposta. As exceções são correções de segurança e de integridade, todas declaradas na seção *Breaking changes* de cada relatório. Resumo:

| Projeto | Mudança de contrato | Finding que a motivou |
|---|---|---|
| 1 | `POST /admin/query` e `POST /admin/reset-db` **removidos** — executavam SQL arbitrário e apagavam as 4 tabelas, sem autenticação | 2 |
| 1 | `GET /usuarios` e `/usuarios/<id>` não devolvem mais `senha`; `/health` não devolve mais `secret_key`, `debug`, `db_path` nem `ambiente` | 2 |
| 1 | Respostas 500 devolvem `{"erro": "Erro interno"}` em vez da mensagem da exceção | 10 |
| 1 | **Autenticação obrigatória em 13 das 17 rotas** — só `POST /login`, `POST /usuarios`, `GET /` e `GET /health` respondem sem token. Sem token, `401`; com papel insuficiente, `403`. `POST /login` passa a devolver o campo aditivo `token` | 4 |
| 2 | `GET /api/admin/financial-report` e `DELETE /api/users/:id` passam a exigir `X-Admin-Api-Key` | 5 |
| 2 | `POST /api/checkout` valida senha (mín. 8), e-mail e cartão — payloads antes aceitos respondem 400 | 4, 12 |
| 3 | **Autenticação obrigatória em 18 das 22 rotas** — só `POST /login`, `POST /users`, `GET /` e `GET /health` respondem sem token. Sem token, `401`; com papel insuficiente, `403` | 2 |
| 3 | `password` removido das respostas de `/users` e do objeto `user` de `POST /login` | 1 |
| 3 | Política de senha de 4 para 8 caracteres mínimos | 2 |

> Duas consequências operacionais registradas nos relatórios: a `SECRET_KEY` do projeto 1 **continua no histórico do Git e precisa ser rotacionada** — removê-la do código não basta; e no projeto 3 os hashes MD5 gravados não são verificáveis pelo scrypt, então bancos existentes exigem `python seed.py` ou reset de senha.

---

## Revisão pós-devolutiva

Duas rodadas de devolutiva, dois defeitos da **mesma família** — a Fase 3 fechando
um finding de autenticação pela metade e o relatório dando o item por resolvido.
Nas duas vezes o conserto começou pela skill, e só depois pelo projeto.

### Primeira devolutiva — o guard atrás da flag (`task-manager-api`)

A primeira entrega recebeu do instrutor uma devolutiva precisa:

> A infraestrutura de autenticação que a Fase 3 construiu no `task-manager-api` está bem feita, mas fica desligada por padrão: `AUTH_REQUIRED=false` no `.env.example` e no `settings.py`, e todo guard do `auth.py` só barra quando essa flag está ligada, então o `DELETE /users/` segue aberto sem token, que é justamente o impacto do CRITICAL 2 do seu relatório. Ajuste a regra de preservação de comportamento e o playbook para tratar exigir autenticação como breaking change de segurança, igual você já fez com a remoção do campo de senha, e rode a skill de novo nesse projeto.

O diagnóstico estava certo, inclusive na ordem das causas: **o defeito era da skill**, e o projeto era só onde ele aparecia. Por isso a revisão começou pela skill.

#### O que mudou na skill

A skill é idêntica nas três cópias (`code-smells-project/`, `ecommerce-api-legacy/`, `task-manager-api/`); todas foram atualizadas.

| Arquivo | Mudança |
|---|---|
| `SKILL.md` — regra 4 | *"Comportamento preservado"* → *"Comportamento preservado — **menos onde preservá-lo é preservar a falha**"*. A correção de segurança deixou de ser "exceção permitida" e virou obrigação, com a lista do que entra: remover campo sensível, remover endpoint sem controle, **exigir autenticação em rota que hoje responde sem credencial**, endurecer validação insegura. Um parágrafo novo proíbe nominalmente o padrão que causou o problema — `AUTH_REQUIRED=false`, `ENABLE_AUTH=0`, `if (config.authEnabled)` — e fecha com o paralelo que torna a regra difícil de contornar: remover `password` da resposta também quebra clientes, e ninguém propõe `RETURN_PASSWORD=true` |
| `SKILL.md` — Fase 3, passo 5 | Recusa explícita de duas justificativas: *"resolver mudaria o contrato"* e *"o controle está implementado, basta ligar"*. Vale o comportamento com os defaults versionados, não o comportamento possível |
| `SKILL.md` — Fase 3, passo 6 | Nova exigência de validação: provar controle de segurança **pela resposta**, com a app subida nos defaults versionados, chamando rota sensível sem credencial e rota privilegiada com credencial de menor privilégio, e colando os status obtidos |
| `references/refactoring-playbook.md` — RP-04 | Seção nova de ~60 linhas: *"Exigir o token é breaking change — e é para ser feito assim mesmo"*. Traz o antes/depois do guard inerte contra o guard incondicional (em Python e em Express), a tabela do escopo público mínimo, o texto pronto da seção *Breaking changes* e o bloco de chamadas que serve de prova |
| `references/antipattern-catalog.md` — AP-04 | Subseção *"Controle de acesso presente e desligado"*, com três greps de detecção (default no `.env`, default no módulo de config, guard dentro de `if` de configuração) e a instrução de classificar como **CRITICAL**, não como MEDIUM de configuração |
| `references/architecture-guidelines.md` | *Defaults seguros* passou a incluir **autenticação exigida**, mais a regra geral: configuração escolhe *qual* segredo e *qual* TTL, nunca *se* a verificação acontece |
| `references/report-template.md` | O exemplo de *Breaking changes* ganhou a exigência de token; a lista de *erros que invalidam o relatório* ganhou o item de marcar como resolvido um finding cujo controle está desligado nos defaults |

#### O que a skill reprocessada encontrou

Rodada de novo no `task-manager-api`, a Fase 2 acusou o problema pelos greps novos — sete pontos: o default no `.env.example`, o default no `settings.py` e os cinco guards condicionados em `auth.py`. A confirmação veio da requisição real, com a aplicação nos defaults versionados: **as 22 rotas respondiam sem nenhuma credencial**, `DELETE /users/3` incluído.

#### O que mudou no projeto

| Arquivo | Mudança |
|---|---|
| `src/config/settings.py` | `AUTH_REQUIRED` **removida** — não desligada, removida. Sobra `TOKEN_TTL_SECONDS`, que é parâmetro, não interruptor |
| `.env.example` | A variável saiu; no lugar ficou o comentário que explica que autenticação não é opcional e quais são as rotas públicas |
| `src/middlewares/auth.py` | Os cinco `if settings.AUTH_REQUIRED` sumiram. Sem nada configurável, os decorators pararam de receber `settings`, e a resolução de identidade foi concentrada em `_require_identity()` |
| `src/views/routes.py` | As 10 rotas de leitura, antes abertas, passaram a exigir token. As 4 rotas públicas ficaram declaradas em `PUBLIC_ROUTES`, com o motivo de cada uma ao lado — a decisão passou a ser legível no código, em vez de implícita na ausência de decorator |
| `src/app.py` | `build_blueprints(controllers, settings)` → `build_blueprints(controllers)` |
| `task-manager-api/README.md` | Seção *Autenticação* reescrita: tabela das rotas públicas, exemplo de `curl` com token, e a nota de por que não existe flag |
| `reports/audit-project-3.md` | Finding 2 passou de ⚠️ Parcial para ✅ Resolvido, com a evidência do antes e do depois; *Breaking changes* ganhou a exigência de autenticação como item 1; e a árvore de estrutura foi remedida com `wc -l` (trazia 2.171 linhas e 177 como maior arquivo; o real já era 2.337 e 188 antes desta rodada) |

**Escopo escolhido: tudo autenticado, menos login, registro e liveness.** Exigir token só nas escritas fecharia o `DELETE /users/<id>` da devolutiva, mas deixaria `GET /users` entregando a lista de e-mails de todos os usuários e `GET /reports/summary` entregando a produtividade de cada um para qualquer anônimo — os dois estão citados no *Impacto* do finding 2. Parar nas escritas seria fechar o finding pela metade outra vez.

#### Antes e depois, medido

Mesmo probe, mesma aplicação, sem nenhuma credencial:

| | Antes | Depois |
|---|---|---|
| `GET /tasks` | 200 | **401** |
| `GET /users` | 200 | **401** |
| `GET /reports/summary` | 200 | **401** |
| `POST /tasks` | 201 | **401** |
| `PUT /users/1` | 200 | **401** |
| **`DELETE /users/3`** | **200** | **401** |
| `GET /` | 200 | 200 |
| `GET /health` | 200 | 200 |
| `POST /login` | 200 | 200 |
| `POST /users` (registro) | 201 | 201 |

18 rotas passaram a exigir token; as 4 públicas seguem abertas por decisão declarada.

| Verificação da segunda execução | Resultado |
|---|---|
| Rotas protegidas sem token | ✅ 18/18 respondem `401` |
| Rotas públicas sem token | ✅ 4/4 respondem normalmente |
| Matriz de autorização | ✅ 17/17 — token ausente, adulterado, esquema errado, papel insuficiente, escalada de privilégio e caminhos permitidos |
| Contrato preservado sob token válido | ✅ **26/26** idênticos em status e forma de resposta contra a versão anterior rodando em paralelo na porta 5001, sobre bancos recém-seedados idênticos |
| Rotas registradas | ✅ 22 — as mesmas 22 |
| Varredura dos greps novos do AP-04 | ✅ 0 ocorrências em código executável |

A comparação lado a lado é o ponto que fecha a devolutiva: **dado um token válido, as duas versões respondem exatamente a mesma coisa em 26/26 casos** — leituras, escritas, `404`, `400` de validação, `401` de credencial inválida e paginação. A única diferença de comportamento é a exigência do header. É o que caracteriza a mudança como breaking change de segurança bem delimitado, e não como refatoração que alterou o contrato por descuido.

---

### Segunda devolutiva — o gate que nunca chegou a existir (`code-smells-project`)

A rodada seguinte recebeu esta devolutiva:

> No `code-smells-project` o finding 4 do `audit-project-1.md` está marcado como resolvido, mas nenhuma rota do projeto exige credencial e o `GET /relatorios/vendas` continua aberto, que é justamente o impacto descrito no próprio finding. Reforce a Fase 3 e o playbook da sua skill para aplicar nesse projeto o mesmo gate de autenticação que ela já aplica no `ecommerce-api-legacy` e no `task-manager-api`, e rode a skill de novo.

Confirmado por medição antes de mexer em qualquer coisa: **17 rotas registradas, 0
com guard**, e `GET /relatorios/vendas` devolvendo `200` com o faturamento da
operação para `curl` sem header nenhum.

**Por que a rodada anterior não pegou isso.** A correção da primeira devolutiva
mirou no *sintoma que apareceu lá*: o guard construído e desligado por flag. Toda
a linguagem nova — os greps do AP-04, a seção de RP-04, o item da lista de erros
do relatório — falava de *controle presente e desligado*. No `code-smells-project`
o controle nunca chegou a ser construído: não havia flag, não havia decorator, não
havia `is_admin()` não chamado. **Não havia nada — e "nada" não casa com nenhum
grep.** A skill tratou o hash `scrypt` e a remoção dos dois `/admin/*` como o
finding inteiro, e o relatório registrou a justificativa que a regra 4 já recusava
por escrito: *"exigir `Authorization` mudaria o contrato de toda chamada de
escrita"*.

O erro de fundo é o mesmo das duas vezes: **conferir o finding pelos sinais que
sobraram no código, em vez de conferir pelo impacto que ele mesmo descreve.** O
campo *Impacto* do finding 4 dizia, desde a primeira versão do relatório, que
qualquer anônimo lia o relatório de faturamento. Bastava tentar.

#### O que mudou na skill (segunda rodada)

| Arquivo | Mudança |
|---|---|
| `SKILL.md` — regra 4 | A exceção de segurança passou a incluir, com todas as letras, o caso *"o projeto legado não tem mecanismo de autenticação nenhum"*: o gate é **construído do zero**, não dispensado por não existir |
| `SKILL.md` — Fase 3, passo 5 (novo) | Passo obrigatório e não condicional: instalar o gate (RP-17) com **inventário de todas as rotas**, cada uma classificada em `público`/`autenticado`/`privilegiado`. Traz a tabela dos três estados possíveis do projeto legado (tem guard parcial / tem login decorativo / não tem nada) e a regra de que remover endpoint administrativo perigoso **não** substitui o gate |
| `SKILL.md` — Fase 3, passo 6 | Novo critério de "Resolvido": **cada frase escrita no campo *Impacto* do finding precisa ter deixado de ser verdade**. Terceira justificativa recusada nominalmente: *"o projeto não tinha autenticação, então não havia o que consertar"* |
| `SKILL.md` — Fase 3, passo 7 | A validação passou a exigir a **matriz de acesso cobrindo 100% das rotas** — o número de linhas tem que bater com o número de rotas registradas |
| `references/refactoring-playbook.md` — **RP-17** (novo) | Transformação nova, *Gate de autenticação por rota*: caso A (projeto sem nenhum mecanismo — antes/depois do `/login` que só devolve o usuário até o `TokenSigner` + decorators), caso B (guard parcial ou atrás de flag), o inventário de rotas como entrega, as quatro regras sem exceção e o bloco de prova por chamada |
| `references/antipattern-catalog.md` — AP-04 | Subseção *"Controle de acesso simplesmente ausente"*: em vez de procurar padrão suspeito, **contar** rotas registradas contra rotas com guard. `0 de 17` é o achado. Registra que um `/login` que não emite credencial vale **zero**, e manda listar no *Impacto* as rotas sensíveis abertas, uma a uma |
| `references/antipattern-catalog.md` — AP-05 | Endpoint de relatório/faturamento aberto virou sinal explícito, no mesmo nível do endpoint destrutivo aberto — era exatamente o que passou batido |
| `references/project-analysis.md` | A Fase 1 passou a medir e imprimir a linha `Auth: <N> de <M> rotas exigem credencial`. O `0 de 17` aparece como fato descritivo já na primeira fase, antes de qualquer julgamento |
| `references/architecture-guidelines.md` | Camada *Middlewares* ganhou o gate (deny-by-default, lista de públicas no arquivo de rotas); o checklist da Fase 3 ganhou 4 itens de acesso; a seção de validação ganhou o script pronto da matriz |
| `references/report-template.md` | Seção *Matriz de acesso por rota* como parte obrigatória do resultado; dois erros novos que invalidam o relatório — marcar finding de auth como resolvido com alguma rota não pública aberta, e matriz que cobre menos rotas do que a aplicação registra |

#### O que mudou no projeto

| Arquivo | Mudança |
|---|---|
| `src/infrastructure/security.py` *(novo)* | `TokenSigner`: JWT HS256 assinado com a `SECRET_KEY` e com expiração, montado com a stdlib (`hmac`+`hashlib`+`base64`) — nenhuma dependência nova. Recebe segredo e TTL por injeção |
| `src/middlewares/auth.py` *(novo)* | `exigir_autenticacao`, `exigir_admin`, `exigir_dono_ou_admin(param)` e `exigir_dono_no_corpo(campo)`. Sem flag: o guard vale sempre |
| `src/views/routes.py` | As 17 rotas passaram a declarar seu gate na própria linha do mapeamento; as 4 públicas ficaram em `ROTAS_PUBLICAS`, com o motivo de cada uma |
| `src/services/usuario_service.py` · `controllers/usuario_controller.py` | `POST /login` passou a emitir o token, devolvido no campo aditivo `token` — as chaves antigas do corpo seguem iguais |
| `src/domain/errors.py` | `AutenticacaoError` (401) e `PermissaoError` (403) |
| `src/config/settings.py` · `.env.example` | `TOKEN_TTL_SECONDS` (parâmetro). Nenhuma variável liga ou desliga a verificação |
| `src/app.py` | Constrói o `TokenSigner` e o injeta; o middleware lê de `app.extensions`, não importa `settings` |
| `code-smells-project/README.md` | Seção *Autenticação* com exemplo de `curl` e tabela de acesso por rota |
| `reports/audit-project-1.md` | Finding 4 refeito: o *Impacto* passou a listar as rotas abertas uma a uma; a "nota de escopo" que justificava não implementar autenticação foi substituída pelo registro do que estava errado; seção *Matriz de acesso por rota* nova; *Breaking changes* ganhou o item 6 |

**Escopo escolhido: tudo autenticado, menos login, registro e liveness.** Fechar só
`GET /relatorios/vendas` atenderia a devolutiva ao pé da letra e deixaria
`GET /usuarios` entregando nome e e-mail de todos os clientes e `GET /pedidos`
entregando o histórico de compras de qualquer pessoa — as duas coisas estão
escritas no *Impacto* do finding 4. É o mesmo critério aplicado no
`task-manager-api` na rodada anterior.

#### Antes e depois, medido

As duas versões subidas lado a lado (a de `HEAD` sem gate na porta 5098, a
refatorada na 5099), bancos recriados do zero, as **17 rotas** chamadas com três
credenciais:

| | Antes (anônimo) | Depois (anônimo) | Cliente | Admin |
|---|:--:|:--:|:--:|:--:|
| **`GET /relatorios/vendas`** | **200** | **401** | **403** | 200 |
| `GET /usuarios` | 200 | **401** | **403** | 200 |
| `GET /pedidos` | 200 | **401** | **403** | 200 |
| `PUT /pedidos/<id>/status` | 200 | **401** | **403** | 200 |
| `POST` / `PUT` / `DELETE /produtos` | 201 / 200 / 200 | **401** | **403** | 201 / 200 / 200 |
| `GET /produtos`, `/produtos/busca`, `/produtos/<id>` | 200 | **401** | 200 | 200 |
| `GET /usuarios/<id>`, `GET /pedidos/usuario/<id>` | 200 | **401** | 200 (próprio) / **403** (outro) | 200 |
| `POST /pedidos` | 201 | **401** | 201 (próprio) / **403** (outro) | 201 |
| `GET /`, `GET /health`, `POST /login`, `POST /usuarios` | 200/200/200/201 | igual | igual | igual |

| Verificação da segunda execução | Resultado |
|---|---|
| Rotas registradas | ✅ 17 — as mesmas 17 |
| Matriz de acesso | ✅ 17/17 rotas conferidas pela chamada; 13 exigem credencial, 4 públicas declaradas |
| Rotas de negócio sem token | ✅ 13/13 respondem `401` |
| Privilégio insuficiente | ✅ `403` em 8 rotas de admin com token de cliente; `403` em dono-ou-admin lendo terceiro |
| Token adulterado / sem `Bearer` / vazio / expirado / assinado com outra chave | ✅ `401` nos cinco casos |
| Contrato preservado sob credencial válida | ✅ **25/25** chamadas idênticas em status e corpo contra a versão sem gate rodando em paralelo |
| Varredura por flag que desligue auth | ✅ 0 ocorrências |

**Dado o token, as duas versões respondem exatamente a mesma coisa em 25/25 casos.**
O gate mudou quem pode chamar, não o que a API responde a quem pode.

---

## Como Executar

### Pré-requisitos

| Requisito | Versão | Usado por |
|---|---|---|
| [Claude Code](https://docs.claude.com/en/docs/claude-code) | atual | os três projetos (é a ferramenta que executa a skill) |
| Python | 3.10+ | `code-smells-project`, `task-manager-api` |
| Node.js | 18+ | `ecommerce-api-legacy` |
| `curl` | qualquer | validação manual dos endpoints |

A skill não instala dependências: instale as de cada projeto antes de rodar a Fase 3, senão a validação de boot falha.

### A skill já está nos três projetos

`.claude/skills/refactor-arch/` está versionada dentro de `code-smells-project/`, `ecommerce-api-legacy/` e `task-manager-api/` — as três cópias são idênticas. Não é preciso copiar nada. Se quiser conferir:

```bash
diff -r code-smells-project/.claude/skills/refactor-arch \
        task-manager-api/.claude/skills/refactor-arch     # sem saída = idênticas
```

Skills de projeto são descobertas a partir do diretório onde o Claude Code é aberto — por isso o `cd` em cada projeto é parte do procedimento, não conveniência.

### Projeto 1 — code-smells-project (Python/Flask)

```bash
cd code-smells-project
pip install -r requirements.txt
claude "/refactor-arch"
```

Esperado: Fase 1 detecta `Python` + `Flask 3.1.1`, domínio de e-commerce e 4 arquivos-fonte. Fase 2 emite o relatório e **pausa** em `Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para liberar a refatoração.

### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

```bash
cd ../ecommerce-api-legacy
npm install
claude "/refactor-arch"
```

Esperado: Fase 1 detecta `JavaScript` + `Express ^4.18.2` e o domínio de **LMS com checkout** (cursos, matrículas, pagamentos) — não "e-commerce", apesar do nome da pasta.

### Projeto 3 — task-manager-api (Python/Flask)

```bash
cd ../task-manager-api
pip install -r requirements.txt
python seed.py
claude "/refactor-arch"
```

Esperado: Fase 1 detecta `Python` + `Flask 3.0.0` com SQLAlchemy e o domínio de Task Manager. Fase 2 deve encontrar problemas **mesmo com o projeto já dividido em pastas** — a concentração esperada está em regra de negócio no handler, `except:` nu, N+1, duplicação e camada morta.

> Rode o `seed.py` **antes** do primeiro boot: sem ele o banco fica vazio e a validação de endpoints da Fase 3 não distingue "lista vazia" de "quebrou".

### Como validar que a refatoração funcionou

**1. A aplicação sobe.**

```bash
# Python
python app.py            # esperado: servidor em http://localhost:5000, sem traceback

# Node
npm start                # esperado: servidor em http://localhost:3000, sem stack trace
```

**2. Os endpoints originais respondem igual.**

```bash
# code-smells-project
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:5000/produtos
curl -s http://localhost:5000/produtos/1
curl -s http://localhost:5000/pedidos

# ecommerce-api-legacy — payloads prontos em api.http
curl -s -X POST http://localhost:3000/api/checkout \
  -H 'Content-Type: application/json' \
  -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
curl -s http://localhost:3000/api/admin/financial-report

# task-manager-api
curl -s http://localhost:5000/tasks
curl -s http://localhost:5000/reports/summary
```

Compare **status** e **forma da resposta** (as chaves do JSON) com o comportamento anterior à refatoração. Valores voláteis — ids autoincrementais, timestamps — não contam como diferença.

**3. A estrutura MVC existe.**

```bash
tree src -L 2      # esperado: config/ models/ services/ controllers/ views|routes/ middlewares/
```

**4. Os anti-patterns sumiram.**

```bash
# nenhum segredo literal restante
grep -rniE "(secret|password|api[_-]?key)\s*[:=]\s*['\"]" src/

# nenhuma query por concatenação
grep -rnE "(execute|query|run)\(.*(\+|\$\{|f\")" src/

# nenhum except nu / console.log de log
grep -rn "except:" src/ ; grep -rn "console\.log(" src/
```

Saída vazia nos quatro comandos é o resultado esperado. A única exceção é o `grep "except:"` em `task-manager-api/`, que devolve duas linhas de *docstring* (`src/domain/errors.py:6` e `src/middlewares/error_handler.py:3`) citando o anti-pattern removido para documentar por que a camada existe — não há `except:` nu em código executável.

**5. O relatório foi salvo.**

```bash
ls reports/        # audit-project-1.md, audit-project-2.md, audit-project-3.md
```

Cada relatório deve trazer a seção "Resultado da Refatoração" com o log real do boot e das chamadas — não uma descrição do log.