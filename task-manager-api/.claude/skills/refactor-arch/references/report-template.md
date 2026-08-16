# Template do relatório de auditoria (Fase 2)

Dois formatos, mesmo conteúdo:
- **A** — bloco impresso no terminal ao fim da Fase 2 (é o que o usuário lê para decidir).
- **B** — arquivo `reports/audit-<projeto>.md`, salvo **depois** da confirmação.

---

## A. Saída no terminal

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

Findings

[CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL,
             validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

[CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
Impact: Segredo versionado no histórico do Git; rotacionar o valor não
        remove o commit. Permite forjar sessões assinadas.
Recommendation: Mover para variável de ambiente com .env.example versionado.

...

Deprecated APIs: 2 ocorrências (datetime.utcnow, Model.query.get)

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

### Regras do bloco

1. **Ordem:** CRITICAL → HIGH → MEDIUM → LOW. Dentro do mesmo nível, o de maior alcance primeiro.
2. **`File:`** é obrigatório e sempre com linha real: `arquivo.ext:47` ou `arquivo.ext:171-201`. Quando o mesmo padrão ocorre em muitos pontos, cite 3-4 exemplos com linha e some o resto: `models.py:28, :47-50, :109-111 (+11 ocorrências)`.
3. **Quatro campos por finding**, nesta ordem, sem exceção:
   - `Description:` — o que está no código, factual, com o valor literal quando ajudar (`SECRET_KEY hardcoded como '...'`).
   - `Impact:` — a consequência concreta. Nada de "é ruim para a manutenção": diga *o que quebra*, *quem vê o dado*, *quantas queries a mais*.
   - `Recommendation:` — a ação de correção, apontando o padrão do playbook quando existir.
4. **Título do finding** = nome do anti-pattern do catálogo (em inglês, como no catálogo), não uma frase livre.
5. A linha `Deprecated APIs:` é **obrigatória**, mesmo quando o resultado é `nenhuma ocorrência encontrada`.
6. `Total:` bate com a soma do `Summary`. Confira antes de imprimir.
7. `Files:` e as contagens vêm de comando executado, não de estimativa.
8. Indentação de continuação: alinhe com a primeira letra do texto do campo (como no exemplo acima).

---

## B. Arquivo em `reports/`

Caminho e nome seguem a regra "Onde salvar o relatório" do `SKILL.md` — `reports/` na **raiz do repositório**, com o nome vindo do pedido do usuário, da convenção já existente na pasta, ou do nome do diretório do projeto.

Mesmo conteúdo, em Markdown, com o cabeçalho de contexto e as seções de fechamento.

```markdown
# Relatório de Auditoria Arquitetural — <nome-do-projeto>

| | |
|---|---|
| **Projeto** | code-smells-project |
| **Stack** | Python 3.x + Flask 3.1.1 |
| **Domínio** | E-commerce API (produtos, pedidos, usuários) |
| **Arquitetura atual** | Monolítica — 4 arquivos, sem separação de camadas |
| **Arquivos analisados** | 4 (~800 linhas) |
| **Data** | AAAA-MM-DD |
| **Skill** | refactor-arch v1 |

## Resumo

| Severidade | Qtd. |
|---|---|
| CRITICAL | 4 |
| HIGH | 5 |
| MEDIUM | 2 |
| LOW | 3 |
| **Total** | **14** |

## Findings

### [CRITICAL] 1. SQL Injection — queries montadas por concatenação

- **Anti-pattern:** AP-01
- **Arquivo(s):** `models.py:28`, `models.py:47-50`, `models.py:109-111` (+11 ocorrências)

**Descrição**
<o que está no código, com o trecho literal quando ajudar>

```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
```

**Impacto**
<consequência concreta e verificável>

**Recomendação**
<ação + referência ao padrão do playbook: "→ RP-01">

---

### [CRITICAL] 2. ...

## APIs deprecated

| Arquivo:linha | API | Substituto |
|---|---|---|
| `models/task.py:52` | `datetime.utcnow()` | `datetime.now(timezone.utc)` |

_(ou: "Nenhuma ocorrência encontrada.")_

## Cobertura da varredura

Anti-patterns verificados: 19/19. Ausentes neste projeto: AP-08, AP-09, AP-15.

## Resultado da Refatoração

_(preenchido ao fim da Fase 3 — ver abaixo)_
```

### Seção "Resultado da Refatoração" (acrescentada na Fase 3)

```markdown
## Resultado da Refatoração

### Estrutura antes → depois

<árvore antes> → <árvore depois>

### Findings resolvidos

| # | Severidade | Finding | Status | Onde foi resolvido |
|---|---|---|---|---|
| 1 | CRITICAL | SQL Injection | ✅ Resolvido | `src/models/produto_model.py` — 100% das queries parametrizadas |
| 4 | LOW | Magic numbers | ⚠️ Parcial | faixas extraídas para `src/config/constants.py`; 2 literais mantidos em X |

### Validação

| Verificação | Resultado |
|---|---|
| Aplicação sobe sem erro | ✅ `flask run` — sem traceback |
| Endpoints originais respondem | ✅ 16/16 endpoints, mesmo status e mesma forma de resposta |
| Varredura final do catálogo | ✅ 0 anti-patterns CRITICAL/HIGH remanescentes |

<log real do boot e das chamadas — colar a saída, não parafrasear>

### Breaking changes (correções de segurança)

- `GET /usuarios` não devolve mais o campo `senha`.
- `POST /admin/query` removido (execução de SQL arbitrário sem autenticação).
```

---

## Erros que invalidam o relatório

- Finding sem número de linha, ou com linha que não corresponde ao código.
- Contagem do `Summary` diferente do `Total`.
- Findings fora da ordem de severidade.
- Ausência da linha/seção de APIs deprecated.
- Marcar validação como ✅ sem ter executado o boot e as chamadas.
- Inflar a contagem repetindo o mesmo achado em ocorrências separadas.
