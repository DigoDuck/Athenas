import { useEffect, useState } from "react";

import {
  AppShell,
  Breadcrumb,
  Button,
  Callout,
  CardsDueBadge,
  GeneratedByBadge,
  Icon,
  Inline,
  List,
  ListRow,
  Markdown,
  Panel,
  Popover,
  ProgressBar,
  ReviewFlagBadge,
  Select,
  Stack,
  StateMessage,
  StudyStatusBadge,
  Switch,
  Tabs,
  Tag,
  TextArea,
  TextField,
} from "../ui/index.js";
import "./showcase.css";

// Dev-only page (open /#design in dev mode) to check the base components by eye and keyboard.

const navItems = [
  { id: "inicio", label: "Início", icon: "home", href: "#design" },
  { id: "biblioteca", label: "Biblioteca", icon: "library", href: "#design" },
  { id: "roadmap", label: "Roadmap", icon: "roadmap", href: "#design" },
  { id: "revisoes", label: "Revisões", icon: "reviews", href: "#design" },
];
const secondaryItems = [{ id: "config", label: "Configurações", icon: "settings", href: "#design" }];

const scenes = [
  { value: "none", label: "Mármore (telas internas)" },
  { value: "home", label: "Panorama (Início e Roadmap)" },
];

const colors = [
  ["background", "Mármore"],
  ["surface", "Superfície"],
  ["surface-muted", "Superfície auxiliar"],
  ["heading", "Títulos"],
  ["text", "Texto"],
  ["text-muted", "Texto secundário"],
  ["ink", "Tinta (leitura e navegação)"],
  ["ink-muted", "Tinta secundária"],
  ["primary", "Ação principal"],
  ["board", "Quadro sobre o panorama"],
  ["border", "Separador"],
  ["control-border", "Contorno de controle"],
  ["gold", "Ouro (decorativo)"],
  ["sunset", "Pôr do sol (decorativo)"],
  ["amber", "Âmbar (decorativo)"],
  ["copper", "Cobre (decorativo)"],
  ["bronze", "Bronze"],
  ["rust", "Ferrugem (onde o leitor está)"],
  ["selected", "Seleção"],
  ["success", "Sucesso"],
  ["error", "Erro"],
  ["warning", "Alerta"],
  ["info", "Informação"],
];

const markdownSample = `### Quando usar
**Polimorfismo** deixa o código chamar \`falar()\` sem saber a classe. Veja a [documentação](https://docs.python.org/3/tutorial/classes.html).

1. Uma interface, *vários* comportamentos.
2. Menos condicionais espalhados.
   - Cada classe cuida do seu caso.

> **Na prática:** prefira composição quando a relação for "tem um".

| Abordagem | Risco |
| --- | --- |
| Herança | acoplamento forte |
| Composição | mais código de ligação |`;

function Section({ title, children }) {
  return (
    <section className="showcase__section">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

export default function Showcase() {
  const [tab, setTab] = useState("explicacao");
  const [focusMode, setFocusMode] = useState(false);
  const [scene, setScene] = useState("none");
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState("");

  useEffect(() => {
    document.documentElement.dataset.focusMode = focusMode ? "on" : "off";
  }, [focusMode]);

  function save() {
    setSaving(true);
    setTimeout(() => setSaving(false), 1500);
  }

  const sceneSelect = (
    <Select
      label="Cenário"
      options={scenes}
      value={scene}
      onChange={(event) => setScene(event.target.value)}
    />
  );

  // The panorama: opening lines on its light left side, everything else on opaque panels.
  if (scene === "home") {
    return (
      <AppShell items={navItems} secondaryItems={secondaryItems} current="inicio" scene="home">
        <div className="showcase__home">
          <Panel raised aria-labelledby="retomar">
            <Stack>
              <h2 id="retomar">Retomar o estudo</h2>
              <p>Polimorfismo · Programação orientada a objetos</p>
              <ProgressBar label="Progresso do conceito" value={2} max={5} />
              <Inline>
                <Button>Continuar</Button>
              </Inline>
              {sceneSelect}
            </Stack>
          </Panel>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell
      items={navItems}
      secondaryItems={secondaryItems}
      current="biblioteca"
      scene={scene === "none" ? null : scene}
    >
      <div className="showcase">
        <header className="showcase__header">
          <p className="t-eyebrow">Athenas · Design system v1</p>
          <h1 className="t-display">Componentes base</h1>
        </header>

        <Section title="Cores">
          <ul className="showcase__swatches">
            {colors.map(([token, label]) => (
              <li key={token}>
                <span className="showcase__swatch" style={{ background: `var(--color-${token})` }} />
                <span>{label}</span>
                <code>--color-{token}</code>
              </li>
            ))}
          </ul>
        </Section>

        <Section title="Tipografia">
          <p className="t-display">Aprender, passo a passo.</p>
          <p className="t-page-title">Título da página</p>
          <p className="t-section-title">Título de seção</p>
          <div className="t-reading">
            <p>
              Leitura em 18 px com entrelinha 1,65 e no máximo 66 caracteres por linha. Uma mesma
              operação pode apresentar comportamentos diferentes conforme o objeto que a recebe.
            </p>
            <pre>
              <code>{'class Cachorro extends Animal {\n  emitirSom() { return "Latido"; }\n}'}</code>
            </pre>
          </div>
          <p>Interface em 16 px: Continuar estudo.</p>
          <p className="t-meta">Metadados em 14 px: Em andamento.</p>
        </Section>

        <Section title="Botões">
          <div className="showcase__row">
            <Button iconEnd="arrow-right">Continuar estudo</Button>
            <Button variant="secondary">Revisar</Button>
            <Button variant="tertiary">Ver fontes</Button>
            <Button variant="destructive">Excluir</Button>
            <Button disabled>Continuar</Button>
            <Button loading={saving} onClick={save}>
              Salvar conceito
            </Button>
          </div>
        </Section>

        <Section title="Campos">
          <div className="showcase__grid">
            <TextField
              label="Nome do conceito"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              error={name ? undefined : "Informe o nome do conceito."}
            />
            <TextField label="Área" help="Por exemplo: Programação." />
          </div>
          <TextArea
            label="Explique com suas palavras"
            placeholder="Escreva aqui sua explicação…"
            status="Rascunho salvo às 14:32"
          />
          <div className="showcase__grid">
            <Select
              label="Nível"
              defaultValue=""
              options={[
                { value: "", label: "Não definido" },
                { value: "iniciante", label: "Iniciante" },
                { value: "intermediario", label: "Intermediário" },
              ]}
            />
            <Select
              label="Conceito"
              placeholder="Escolha um conceito"
              defaultValue=""
              help="Só aparecem conceitos fora da trilha."
              options={[
                { value: "1", label: "Polimorfismo (POO)" },
                { value: "2", label: "Herança (POO)" },
              ]}
            />
          </div>
        </Section>

        <Section title="Espaçamento">
          <Panel>
            <Stack gap={2}>
              <h3>Nova área</h3>
              <p className="t-meta">Stack empilha com um passo da escala; Inline põe lado a lado e quebra linha.</p>
            </Stack>
            <form onSubmit={(e) => e.preventDefault()}>
              <Inline gap={3} align="end">
                <div className="showcase__grow">
                  <TextField label="Nome da área" />
                </div>
                <Button type="submit">Adicionar área</Button>
              </Inline>
            </form>
            <Inline justify="between">
              <span className="t-meta">3 áreas</span>
              <Button variant="tertiary">Ver todas</Button>
            </Inline>
          </Panel>
        </Section>

        <Section title="Navegação">
          <Breadcrumb
            items={[
              { label: "Biblioteca", href: "#design" },
              { label: "POO", href: "#design" },
              { label: "Polimorfismo" },
            ]}
          />
          <Tabs
            label="Seções do subtema"
            value={tab}
            onChange={setTab}
            items={[
              { id: "explicacao", label: "Explicação", content: <p>Conteúdo da explicação.</p> },
              { id: "pratica", label: "Prática", content: <p>Perguntas e explicar com minhas palavras.</p> },
              { id: "caderno", label: "Modo caderno", content: <p>Versão para copiar no caderno.</p> },
            ]}
          />
          <Popover label="Ações da etapa" trigger={<Icon name="more" />}>
            {(close) => (
              <>
                <button type="button" className="ui-popover__item" onClick={close}>
                  Mover para antes
                </button>
                <button type="button" className="ui-popover__item ui-popover__item--danger" onClick={close}>
                  Tirar da trilha
                </button>
              </>
            )}
          </Popover>
        </Section>

        <Section title="Situação e progresso">
          <div className="showcase__row">
            <StudyStatusBadge status="not_started" />
            <StudyStatusBadge status="in_progress" />
            <StudyStatusBadge status="completed" />
            <ReviewFlagBadge />
            <CardsDueBadge />
            <GeneratedByBadge by="claude" />
            <Tag>Iniciante</Tag>
          </div>
          <Panel raised>
            <List label="Subtemas de Orientação a objetos">
              <ListRow
                title="Polimorfismo"
                href="#design"
                meta="Iniciante · Difícil"
                badges={
                  <>
                    <StudyStatusBadge status="in_progress" />
                    <CardsDueBadge />
                  </>
                }
                action={<ProgressBar value={3} max={8} label="Blocos lidos de Polimorfismo" />}
              />
              <ListRow
                title="Herança"
                href="#design"
                meta="Iniciante"
                badges={
                  <>
                    <StudyStatusBadge status="completed" />
                    <ReviewFlagBadge />
                  </>
                }
              />
              <ListRow
                title="Abstração"
                href="#design"
                meta="Intermediário"
                badges={<StudyStatusBadge status="not_started" />}
              />
            </List>
          </Panel>
        </Section>

        <Section title="Destaques do conteúdo">
          <Callout>Uma interface, diferentes comportamentos.</Callout>
          <Callout variant="ai">Linguagens dinâmicas resolvem o método em tempo de execução.</Callout>
          <Callout variant="ai" source="Documentação oficial do Java">
            A anotação @Override confirma a sobrescrita.
          </Callout>
        </Section>

        <Section title="Texto de estudo (Markdown)">
          <div className="t-reading">
            <Markdown text={markdownSample} />
          </div>
        </Section>

        <Section title="Estados">
          <div className="showcase__states">
            <Panel>
              <StateMessage title="Seu primeiro conceito começa aqui." action={<Button>Adicionar conceito</Button>}>
                Adicione um conceito para iniciar seus estudos.
              </StateMessage>
            </Panel>
            <Panel>
              <StateMessage
                kind="error"
                title="Não foi possível salvar."
                action={<Button variant="secondary">Tentar novamente</Button>}
              >
                Seu texto continua aqui.
              </StateMessage>
            </Panel>
            <Panel>
              <StateMessage kind="success" title="Alterações salvas." />
            </Panel>
          </div>
        </Section>

        <Section title="Foco e cenário">
          {sceneSelect}
          <Switch
            label="Modo de foco"
            description="Oculta o cenário e os elementos decorativos."
            checked={focusMode}
            onChange={setFocusMode}
          />
        </Section>
      </div>
    </AppShell>
  );
}
