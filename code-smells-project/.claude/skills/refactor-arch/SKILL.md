---
name: refactor-arch
description: Audita e refatora uma codebase para o padrão MVC, de forma agnóstica de tecnologia. Executa 3 fases sequenciais — análise da stack, auditoria de anti-patterns com relatório por severidade (CRITICAL/HIGH/MEDIUM/LOW) e refatoração para camadas MVC com validação de que a aplicação continua funcionando. Use quando o pedido for auditar arquitetura, encontrar code smells, avaliar violações de MVC/SOLID, ou reestruturar/refatorar um projeto legado para MVC.
---

# Refactor Arch — Auditoria e Refatoração Arquitetural

Você é um arquiteto de software auditando um projeto legado. Sua entrega são **3 fases sequenciais**, executadas nesta ordem, com um portão humano entre a Fase 2 e a Fase 3.

## Regras invioláveis

1. **Nenhuma escrita antes do "y".** Nas Fases 1 e 2 use apenas ferramentas de leitura (`Read`, `Grep`, `Glob`, `Bash` somente-leitura). Não crie, edite, mova ou apague nenhum arquivo do projeto até o usuário confirmar explicitamente a Fase 3. Salvar o relatório em `reports/` também só acontece depois da confirmação, ou se o usuário pedir.
2. **Todo finding tem arquivo e linha reais.** Cite `caminho/arquivo.ext:linha` ou `:linha-linha` conferidos no código. Nunca invente uma linha, nunca reporte um anti-pattern que você não localizou fisicamente. Se não achou, não reporte.
3. **Nada de suposição de stack.** A linguagem, o framework e o banco saem de evidência no repositório (manifesto de dependências + imports), não do nome da pasta.
4. **Comportamento preservado — menos onde preservá-lo é preservar a falha.** A refatoração não muda contrato de API: mesmas rotas, mesmos métodos, mesmos formatos de resposta. A exceção é a **correção de segurança**, e ela não é opcional: quando o contrato atual *é* a vulnerabilidade, o contrato muda, e a mudança é listada explicitamente como *breaking change* no fim da Fase 3. Entram nessa exceção, todas com o mesmo peso:

   - remover campo sensível da resposta (senha, hash, token, segredo, flag de configuração);
   - remover endpoint que executa SQL arbitrário ou destrói dados sem controle de acesso;
   - **exigir autenticação e autorização em rota que hoje responde sem credencial** — inclusive quando isso faz endpoints que devolviam `200` passarem a devolver `401`/`403`, e inclusive quando o projeto legado **não tem mecanismo de autenticação nenhum**: nesse caso o gate é construído do zero (emissão de token no login + middleware de verificação), não dispensado por não existir;
   - endurecer política de senha e validação de entrada que hoje aceita valor inseguro.

   **Uma correção de segurança nunca fica atrás de uma flag desligada por default.** Construir o middleware de autenticação e deixá-lo inerte com `AUTH_REQUIRED=false`, `ENABLE_AUTH=0`, `if (config.authEnabled)` ou equivalente **não** resolve o finding — o endpoint continua aberto com os defaults versionados, e o relatório passa a mentir ao marcar o item como tratado. Se a exigência de credencial é a correção, ela entra **ligada**: sem flag, ou com uma flag que só existe para aumentar o rigor, nunca para removê-lo. O custo para os clientes da API é real e é registrado em *Breaking changes* — exatamente como a remoção do campo de senha, que também quebra quem lia aquele campo e mesmo assim é feita.
5. **Sem alucinação de números.** Contagem de arquivos, de linhas e de findings vem de comando executado (`wc -l`, `find`), não de estimativa.

## Arquivos de referência

Carregue sob demanda, na fase correspondente — não leia todos de uma vez:

| Arquivo | Quando ler |
|---|---|
| `references/project-analysis.md` | Fase 1 — heurísticas de detecção de linguagem, framework, banco, domínio e arquitetura |
| `references/antipattern-catalog.md` | Fase 2 — catálogo de anti-patterns com sinais de detecção e severidade |
| `references/report-template.md` | Fase 2 — formato exato do relatório de auditoria |
| `references/architecture-guidelines.md` | Fase 3 — regras do MVC alvo e estrutura de diretórios por stack |
| `references/refactoring-playbook.md` | Fase 3 — transformações antes/depois por anti-pattern |

---

## FASE 1 — Análise do projeto

**Objetivo:** entender o que é este projeto antes de julgá-lo.

1. Leia `references/project-analysis.md`.
2. Mapeie o repositório: liste os arquivos de código-fonte (excluindo dependências, artefatos e o próprio diretório da skill) e conte linhas com `wc -l`.
3. Leia **todos** os arquivos de código-fonte do projeto. Em projetos grandes (>3.000 linhas), leia integralmente os arquivos de entrada, rotas, models e configuração, e amostre o resto.
4. Detecte: linguagem, framework + versão (do manifesto), dependências relevantes, banco e tabelas/models, domínio da aplicação (inferido das rotas e das entidades), arquitetura atual.
5. Imprima o bloco `PHASE 1: PROJECT ANALYSIS` no formato definido em `references/project-analysis.md`.

Não emita julgamento de qualidade na Fase 1 — ela é descritiva.

---

## FASE 2 — Auditoria

**Objetivo:** cruzar o código lido contra o catálogo e produzir o relatório.

1. Leia `references/antipattern-catalog.md` e `references/report-template.md`.
2. Para **cada** anti-pattern do catálogo, rode os sinais de detecção (grep/leitura) contra a codebase. Marque presente/ausente. Não pule categorias porque o projeto "parece organizado": projetos com pastas `models/`/`services/` costumam esconder violações de camada, camadas mortas e duplicação.
3. Confirme cada candidato lendo o trecho de código e anotando a linha exata. Descarte falso-positivo.
4. Classifique a severidade pela tabela do catálogo. Quando um achado se encaixar em dois níveis, use o critério de impacto: exposição de dado ou impossibilidade de teste em isolamento → sobe de nível.
5. Agrupe achados da mesma raiz em um único finding com sub-itens, em vez de inflar a contagem com 15 ocorrências do mesmo `print`.
6. **Rode obrigatoriamente a checagem de APIs deprecated** (seção correspondente do catálogo). Se não houver nenhuma, diga isso explicitamente no relatório.
7. Emita o relatório no formato de `references/report-template.md`, com findings ordenados CRITICAL → HIGH → MEDIUM → LOW.
8. Metas mínimas de qualidade da auditoria: **≥ 5 findings** e **≥ 1 CRITICAL ou HIGH**. Se você ficou abaixo disso, não invente achados — volte ao passo 2 e revise as categorias que marcou como ausentes, porque provavelmente a varredura foi rasa.
9. **PARE.** Imprima:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

e aguarde a resposta do usuário. Não prossiga com `n`, com silêncio ou com resposta ambígua. Se o usuário responder algo que não seja uma aprovação clara, trate como `n` e ofereça salvar apenas o relatório.

---

## FASE 3 — Refatoração

Só execute após o `y`.

1. Leia `references/architecture-guidelines.md` e `references/refactoring-playbook.md`.
2. **Capture a linha de base antes de mexer:** suba a aplicação atual e registre a resposta (status + corpo) de cada endpoint existente. Guarde isso — é o critério de "não quebrei nada". Se a aplicação não subir no estado atual, registre isso no relatório e siga em frente.
3. Crie a estrutura de diretórios MVC da stack detectada (`architecture-guidelines.md`).
4. Migre em ordem de dependência, sempre aplicando a transformação correspondente do playbook:
   1. `config/` — toda constante de ambiente e todo segredo saem do código para variáveis de ambiente, com `.env.example` versionado e valores padrão seguros.
   2. `models/` (ou `repositories/`) — acesso a dados por entidade, queries parametrizadas, serialização única por entidade.
   3. `services/` — regra de negócio pura, sem `request`/`response`.
   4. `controllers/` — orquestram: recebem entrada validada, chamam service, devolvem resposta. Sem SQL, sem regra de negócio.
   5. `views/` ou `routes/` — apenas mapeamento rota → controller, mais middleware de validação.
   6. `middlewares/` — error handler central, validação, logging **e o gate de autenticação/autorização do passo 5**.
   7. Entry point / composition root — monta as dependências e injeta; nenhum módulo instancia a própria conexão de banco.
5. **Instale o gate de autenticação — passo obrigatório, não condicional.** Aplique **RP-17** sempre que a Fase 2 tiver registrado AP-04 ou AP-05, ou sempre que existir rota que leia/escreva dado de negócio sem credencial. Vale igualmente para os três casos, sem meio-termo entre eles:

   | Estado do projeto legado | O que a Fase 3 entrega |
   |---|---|
   | Tem token e middleware, mas rota aberta ou flag desligada | Liga o guard, sem flag, e cobre as rotas descobertas |
   | Tem login que devolve o usuário e nada mais | **Cria** a emissão de token no login e o middleware; o login passa a devolver credencial de verdade |
   | Não tem nem login | Cria o mecanismo mínimo (hash + emissão + verificação) antes de fechar as rotas |

   Faça o inventário **de todas as rotas**, uma por linha, e classifique cada uma em `público` / `autenticado` / `privilegiado`. Deny-by-default: uma rota só fica pública se estiver na lista curta justificada de RP-17 (emissão de token, registro da primeira conta, liveness) — e a justificativa vai escrita no relatório, rota por rota. Rota de relatório, faturamento, listagem de usuários, listagem global e escrita **nunca** é pública. Remover um endpoint administrativo perigoso (`/admin/query`, `reset-db`) **não** substitui este passo: as demais rotas sensíveis seguem abertas enquanto o gate não existir.
6. Corrija os findings da Fase 2 conforme o playbook. Todo finding CRITICAL ou HIGH deve estar resolvido ou, se não puder ser, explicitamente justificado no resumo final. Um finding só é **Resolvido** quando **cada consequência descrita no próprio campo *Impacto*** deixou de ser possível — releia o texto que você escreveu na Fase 2 e teste, uma a uma, as frases dele. Se o Impacto diz *"qualquer anônimo lê o relatório de faturamento"*, o finding continua aberto enquanto `GET /relatorios/vendas` responder `200` sem credencial, por mais que o hash de senha e o endpoint de SQL arbitrário já tenham sido tratados. Três justificativas **não** são aceitas:
   - *"resolver mudaria o contrato"* — para finding de segurança, a regra 4 manda mudar o contrato e registrar o breaking change;
   - *"o controle está implementado, basta ligar"* — vale o comportamento com os defaults versionados (`.env.example`, valores default do módulo de config), não o comportamento possível em alguma configuração. Controle desligado é controle ausente;
   - *"o projeto não tinha autenticação, então não havia o que consertar"* — ausência total de controle de acesso é a forma mais grave do finding, não a sua dispensa. Ver o passo 5.
7. **Valide:**
   - a aplicação sobe sem erro (execute o comando de boot da stack e leia o log);
   - cada endpoint da linha de base responde com o mesmo status e a mesma forma de resposta (use `curl`, o `api.http` do projeto, ou os testes existentes);
   - rode uma varredura final dos sinais do catálogo e confirme que os anti-patterns tratados não reaparecem no código novo;
   - **prove os controles de segurança pela resposta, não pelo código.** Com a aplicação subida nos defaults versionados (sem `.env` local, ou com o `.env.example` copiado sem edição), chame cada rota sensível *sem* credencial e cada rota privilegiada com credencial de menor privilégio, e cole os status obtidos. `401`/`403` esperados que voltam `200` significam controle desligado, não controle implementado.
   - **Monte a matriz de acesso e cubra 100% das rotas.** Uma linha por rota registrada — nenhuma omitida —, com o status obtido sem credencial, com credencial comum e com credencial privilegiada. O número de linhas tem que bater com o número de rotas do inventário do passo 5; rota que sobrou de fora da matriz é rota que ninguém testou. Toda linha marcada `público` precisa de uma justificativa na mesma tabela.
   - Se algo falhar, **corrija antes de declarar sucesso**. Nunca reporte validação verde sem ter executado o boot e as chamadas.
8. Imprima o bloco `PHASE 3: REFACTORING COMPLETE` com a nova árvore de diretórios, o resultado real da validação (matriz de acesso incluída) e a lista de breaking changes de segurança (se houver).
9. Salve o relatório de auditoria, agora acrescido da seção "Resultado da Refatoração".

### Onde salvar o relatório

O destino é `reports/` **na raiz do repositório**, não dentro do diretório do projeto:

```bash
git rev-parse --show-toplevel     # raiz do repo; se não for um repo git, use o diretório do projeto
```

Quando o repositório reúne vários projetos, os relatórios dos três ficam no mesmo `reports/` — é o que o leitor espera encontrar, e salvar em `<projeto>/reports/` espalha a entrega.

Nome do arquivo, nesta ordem de precedência:

1. O nome que o usuário pediu.
2. A convenção já usada pelo `reports/` existente (ex.: se já há `audit-project-1.md`, o próximo é `audit-project-2.md`).
3. `audit-<nome-do-diretório-do-projeto>.md`.

Confirme o caminho final junto com o `y` da Fase 2, antes de escrever qualquer arquivo. Crie o diretório se preciso.

### Sobre remover o código antigo

Os arquivos antigos que foram integralmente migrados devem ser **removidos**, não deixados órfãos ao lado da nova estrutura — código duplicado é pior que código legado. A exceção é o entry point esperado pelo `package.json`/`requirements`/README: mantenha o caminho de execução original funcionando (ex.: `app.py` na raiz virando o composition root que importa de `src/`), ou atualize o manifesto e o README para o novo caminho.
