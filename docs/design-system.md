# Design system

The guide below is Diogo's design system v1, copied verbatim from `athenas-design-system/Guia-do-design-system.md` (the boards it mentions are not versioned).

## Implementation notes

- Tokens live in `frontend/src/styles/tokens.css`. Screens use the variables only, never raw values.
- Base components live in `frontend/src/ui/` (import from `frontend/src/ui/index.js`). In dev mode, `/#design` shows all of them.
- Fonts are self-hosted from `frontend/src/assets/fonts/` (SIL OFL 1.1), latin subset only, so use mode works offline.
- Where the guide and `docs/spec.md` disagree, the spec wins. Diogo confirmed the four adaptations below for v1 on 2026-10-12:
  - The guide's main menu lists "Assistente" and an AI side panel, and the Rubber Duck pattern shows AI feedback. Integrated AI is out of scope for v1 (spec 2.2), so neither is built.
  - The guide's flashcard rating shows "Rever / Com esforço / Com facilidade". The spec has three ratings, errei, parcial and acertei, and no Easy (spec 4.6.2).
  - The guide has one "Revisão pendente" badge. The spec keeps the manual review flag and the automatic "has cards due" indicator separate and never merged (spec 3.2). There are two badges: "Marcado para revisar" and "Cartões para hoje".
  - The guide describes tablet and phone layouts. v1 is desktop only (spec 2.3). Below 1200 px the navigation collapses behind a "Menu" button, so a snapped desktop window still works; no phone screens are designed.
- Backgrounds (`frontend/src/assets/scenes/`, from Diogo's frontend kit) are set by the `scene` prop of `AppShell` (`DECISIONS.md` D-034):
  - `home` and `roadmap` (`home-sunset`, `roadmap-sunset`; the `-1280` copies serve windows up to 1440px): Início and Roadmap, the screens that open the day. The panorama runs under the whole screen, navigation included, with `background-size: cover` from the top center, and a veil fades its left side to marble. Only the navigation and the page's opening lines (title, the current item, its main action) sit on that light side; everything else goes on one opaque board along the bottom.
  - Each panorama has a foliage layer (`home-foliage`, `roadmap-foliage`): the out-of-focus bushes at its bottom right, cut from the same photograph at full size, so the same cover sizing keeps them aligned. It is drawn in front of the page and lets clicks through, so the bushes overlap the board; menus (`z-index` 10) still open above it. A new panorama needs its own foliage layer.
  - `null` (default): every other screen, on plain marble with a hairline beside the navigation and a faint olive-leaf shadow in the top corner (`assets/decor/olive-shadow.webp` as a mask over `--color-shadow-ink`, 42% opacity, slight blur), behind the navigation only, never under study text.
  - Scenes, foliage and the leaf are decorative: hidden in focus mode and in print, invisible to screen readers. v1 is desktop only, so there is no portrait scene.
- The owl emblem is used at every size; there is no simplified small version.
- Not in the guide, added here: success, warning and error tint backgrounds for badges (each pair is at least 5:1), and a darker error for the destructive button hover.
- Also not in the guide (UI polish, 2026-10-17):
  - A subsection title role, 22 px Cormorant (`--text-subsection-title`, `.t-subsection-title`), for a concept inside an area in the Biblioteca. The guide jumps from the 28 px section title to 16 px interface text, which made a concept look like one of its subtopics.
  - A disabled tertiary button stays text only (no `#ECEDE8` fill): a gray block next to text buttons, such as Subir at the top of a track, outweighed the whole row. Filled buttons keep the guide's disabled fill.
  - Creation forms open on demand from a "+" button (`AddForm` in `frontend/src/pages/forms.jsx`): the page action sits at the right of the page title, and a list's action sits under the list. Editors for a row open as an inset well right under that row.
- Also not in the guide (new screens, 2026-10-17, from Diogo's mockups, `DECISIONS.md` D-034):
  - Scale and color (they override the guide's values below): fluid type tokens (`--text-reading` 18 to 24px, `--text-ui` 16 to 18px, `--text-lead`, `--text-hero`, `--text-board-title`), near-black titles (`--color-heading`) with Cormorant 700 (`--weight-bold`) on page titles, the open block and the opening lines, navy ink (`--color-ink`, `--color-ink-muted`) for study text and navigation, forest green for the primary action (`--color-primary`), copper (`--color-copper`) for decorative lines and rust (`--color-rust`) for where the reader is. Buttons are regular weight and 48px tall.
  - Navigation: the items hang on a thin copper line with a ring each; the current page is a forest pill with a sunset icon and a filled amber ring.
  - The way forward on a screen (Continuar leitura, Continuar, Li este bloco e avançar, Voltar ao estudo) is a primary pill whose arrow sits in an amber disc (`--color-amber`). It is still one per screen; secondary actions keep the bronze outline.
  - Início and Roadmap open with a large bold Cormorant line (`--text-hero`) under a small rust uppercase label, then the warm board (`--color-board`, `--radius-board`): a slab whose top right corner steps down into a band that bleeds off the window, with its thickness (`--color-board-edge`) showing under it.
  - Reading: a toolbar under the title holds the block picker (a `Popover` with the list of blocks), "Bloco N de M", the read count and Bloco anterior / Próximo bloco. The block sits on a white sheet with a short copper tab at its top left; "Apoio ao estudo" beside it folds and holds Praticar, the personal review flag and the sources.
  - `Popover` (`frontend/src/ui/Popover.jsx`): a button that opens a small panel under it, closed by Escape or a click outside. Rows inside use `.ui-popover__item`.
- Also not in the guide (reading screen, 2026-10-17, `DECISIONS.md` D-031, layout replaced by D-034): study text renders through `Markdown` (`frontend/src/ui/Markdown.jsx`): Cormorant subheadings, bronze list markers, quotes as a bordered card (never a side stripe), tables with hairline rows, and images with a meta-size caption.

---

## ATHENAS · Design system v1

Direção aprovada: mármore branco, mitologia grega e iluminação dourada de pôr do sol. Athenas e a coruja formam a identidade. O amarelo aparece na luz das imagens e em pequenos destaques; superfícies extensas de leitura permanecem brancas.

Este guia define os valores de referência. As pranchas geradas ilustram a direção; formas, fontes e cores nelas podem variar. Não são componentes funcionais nem evidência de acessibilidade testada no site.

### 1. Cores

| Token | Valor | Uso |
|---|---|---|
| background | #FAF9F6 | Fundo branco mármore |
| surface | #FFFFFF | Leitura, formulários, cartões |
| surface-muted | #F2F2EE | Blocos de código e áreas auxiliares |
| text | #34392F | Texto e ação principal |
| text-muted | #62675D | Texto secundário e metadados |
| border | #DDDCD6 | Separadores decorativos |
| control-border | #85897F | Contorno de controles que precisam ser identificados |
| gold | #B79A52 | Emblemas e ornamentação |
| sunset | #E6AF50 | Referência da luz e pequenos realces |
| bronze | #805C1F | Links, ícones ativos, foco e informações destacadas |
| selected | #F4E7CE | Fundo localizado de seleção |
| success | #456149 | Conclusão e confirmação |
| error | #9D3C32 | Erros e ações destrutivas |
| warning | #77540E | Alertas |
| info | #365D74 | Informação complementar |

Contrastes calculados contra branco: text 11,85:1; text-muted 5,81:1; bronze 6,05:1; success 6,86:1; error 6,72:1. Gold 2,71:1 e sunset 1,98:1 são cores decorativas, inadequadas como texto pequeno sobre branco. Esses cálculos não substituem a verificação das telas implementadas.

Não aplicar um filtro amarelo sobre toda a interface. Não usar somente cor para transmitir estado. Indicadores de progresso usam bronze como parte preenchida; ouro pode ser um detalhe adicional.

### 2. Tipografia

Famílias propostas para implementação: Cormorant Garamond Semibold em títulos; Source Sans 3 no corpo e nos controles; JetBrains Mono em código. A representação nas imagens é aproximada. Validar os arquivos de fonte e acentos no protótipo.

| Papel | Desktop | Celular | Entrelinha |
|---|---|---|---|
| Abertura da página inicial | 56 px | 36 px | 1,10 |
| Título da página | 40 px | 30 px | 1,15 |
| Título de seção | 28 px | 24 px | 1,25 |
| Leitura | 18 px | 18 px | 1,65 |
| Interface | 16 px | 16 px | 1,50 |
| Metadados | 14 px | 14 px | 1,45 |
| Código | 15 px | 14 px | 1,60 |

Corpo de texto com largura entre 60 e 72 caracteres por linha, preferencialmente próximo de 66. Evitar títulos gigantes dentro de telas de prática. Marca e pequenos rótulos podem usar maiúsculas; parágrafos e botões usam capitalização normal. Permitir ampliar o texto sem cortar conteúdo.

### 3. Espaço, formas e camadas

Escala de espaçamento: 4, 8, 12, 16, 24, 32, 48 e 64 px. Controles com altura mínima de 44 px e alvos de toque preferencialmente de 48 px. Botões e campos: raio de 6 px. Painéis: raio de 10 px. Contorno comum: 1 px. Estados não dependem exclusivamente de sombras.

Sombra discreta de painel: 0 4px 16px rgba(52,57,47,0.06). Painéis de leitura opacos. Textura restrita ao fundo externo, cabeçalhos e elementos decorativos; nunca atravessa texto de estudo.

Ícones de interface de 20 ou 24 px, traço de aproximadamente 1,75 px, linguagem consistente e rótulos quando necessários. O emblema completo é reservado à marca; a versão simplificada da coruja é usada em tamanhos pequenos. Testar sua legibilidade a 24 e 32 px.

### 4. Componentes e estados

#### Botões

Primário: fundo text, texto branco. Hover: #242820. Pressionado: #1D211A. Secundário: fundo branco, borda bronze e texto bronze. Terciário: texto bronze com indicação adicional no hover. Destrutivo: fundo error, texto branco, reservado a ações de remoção.

Foco pelo teclado: contorno bronze de 2 px, afastado 2 px. Desabilitado: fundo #ECEDE8, texto #62675D e sem ação. Carregamento: indicador e texto como “Salvando…”, preservando a largura e impedindo envio duplicado. Uma ação principal por contexto.

#### Campos

Rótulo persistente acima do controle, ajuda abaixo quando necessária. O placeholder não substitui o rótulo. Borda control-border no estado padrão e contorno bronze no foco. Erro: borda error, ícone e mensagem objetiva como “Informe o nome do conceito.” Respostas longas usam área de texto ampla com rascunho salvo visível.

#### Navegação e abas

Item ativo: fundo selected localizado, marcador bronze e texto text. Abas usam texto e sublinhado bronze; o ativo também ganha peso. Breadcrumb visível na biblioteca. No celular, permitir rolar a faixa de abas sem esconder a opção ativa.

Menu principal canônico: Início, Biblioteca, Roadmap, Revisões e Assistente. Configurações fica como ação secundária. Os recortes de componentes nas imagens não definem uma segunda estrutura de navegação.

#### Listas, painéis e progresso

Preferir linhas com separadores para bibliotecas e revisões. Cartões são usados quando agrupam uma tarefa ou conteúdo independente. Um item de conceito contém título, subtema, nível, situação e próxima ação. Dificuldade percebida é separada do nível do conteúdo.

Progresso combina barra bronze, texto e contagem. “Concluído” não significa “sem revisão pendente”. O roadmap distingue estudo não iniciado, atual e concluído; a necessidade de revisão é um indicador independente. Não bloquear etapas apenas para criar aparência de jogo.

Revisão pendente usa texto e ícone info sobre fundo #EDF2F5. Não usar vermelho para representar a rotina de revisão.

#### Flashcard e Rubber Duck

Flashcard: fundo branco, uma pergunta, ação “Mostrar resposta” e autoavaliação após a revelação. Evitar inversão 3D obrigatória. Rubber Duck: orientação curta, campo amplo e retorno dividido em “O que você explicou bem”, “O que revisar” e “Próximo passo”. Permitir consultar e contestar o retorno da IA.

#### Assistente e Pomodoro

Assistente fechado por padrão; no desktop, painel lateral de aproximadamente 360 px, quando houver espaço. Se a leitura ficar estreita, abrir em painel sobreposto. No celular, usar tela própria. Identificar o contexto usado pelo assistente. Pomodoro discreto, controles explícitos e sem animação pulsante.

### 5. Layout e adaptação

Desktop a partir de 1200 px: navegação de 224 px, área de trabalho flexível, margem de 32 px. Conteúdo geral com largura máxima de 1440 px; leitura continua limitada pela largura de linha. Painel auxiliar só abre se houver espaço suficiente.

Tablet entre 768 e 1199 px: navegação recolhida acessível por botão com rótulo; margem de 24 px; assistente em sobreposição. Celular abaixo de 768 px: coluna única, margem de 16 px, navegação em menu e roadmap em lista vertical. A decoração nunca causa rolagem horizontal.

Página inicial: cenário de pôr do sol presente, retomada do estudo em primeiro plano, revisões e próximo passo abaixo. Biblioteca: organização em listas e pastas. Estudo: superfície branca, subtemas acessíveis, assistente opcional. Modo de foco oculta o cenário e os elementos decorativos. Modo caderno remove navegação, ornamentos e sombras na impressão.

### 6. Imagens e movimento

Luz baixa de fim de tarde, amarelo dourado localizado, reflexos nas colunas de mármore e sombras naturais na vegetação. Preservar partes brancas da pedra. Evitar coloração sépia uniforme. Athenas com elmo, sem asas; coruja naturalista ou símbolo simplificado.

Não colocar texto diretamente sobre áreas fotográficas detalhadas. Usar painel branco ou uma região realmente uniforme com contraste verificado. Imagens decorativas não recebem foco de teclado.

Transições de 120 a 180 ms apenas para mudanças funcionais. Respeitar a preferência de movimento reduzido. Não usar partículas, paralaxe, folhas animadas, brilho pulsante ou confete automático durante o estudo.

### 7. Estados e linguagem

Vazio: “Seu primeiro conceito começa aqui.” Ação: “Adicionar conceito”. Erro: explicar o problema e a recuperação, sem depender de cor. Exemplo: “Não foi possível salvar. Seu texto continua aqui.” Ação: “Tentar novamente”. Não afirmar salvamento antes de confirmação.

Carregamento: estrutura estável e indicação discreta, sem saltos. Sucesso: confirmação breve, como “Alterações salvas”. Ausência de rotina não gera cobranças. Evitar frases moralizantes sobre disciplina ou produtividade. Usar “Continue de onde parou” e “Uma etapa de cada vez”.

### 8. Verificação antes da implementação ser considerada pronta

Conferir contraste no layout real, navegação por teclado, foco visível, nomes acessíveis, texto ampliado, leitura no celular, estados de erro e recuperação, redução de movimento e recortes das imagens. Nenhuma dessas verificações é substituída pelas imagens deste design system.

