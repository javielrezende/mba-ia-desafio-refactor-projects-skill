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