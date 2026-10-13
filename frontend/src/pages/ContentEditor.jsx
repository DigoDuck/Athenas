import { useEffect, useRef, useState } from "react";

import { api } from "../api.js";
import {
  Badge,
  Button,
  Callout,
  Inline,
  List,
  ListRow,
  Panel,
  Stack,
  StateMessage,
  TextArea,
} from "../ui/index.js";
import { ActionError } from "./forms.jsx";
import "./content.css";

// Paste the subtopic's Markdown, see what the import will make of it, then save (spec 4.2.1).
// Saving needs a preview of the exact text in the field, so nothing is saved unseen.
export default function ContentEditor({ subtopic, onClose }) {
  const url = `/api/subtopics/${subtopic.id}/content/`;
  const [markdown, setMarkdown] = useState("");
  const [loadError, setLoadError] = useState(null);
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(null);
  // Bumped after a save so the pending cards are fetched again.
  const [version, setVersion] = useState(0);

  const panel = useRef(null);
  useEffect(() => panel.current?.focus(), []);

  useEffect(() => {
    let active = true;
    api.get(url).then(
      (content) => active && setMarkdown(content.raw_markdown),
      (e) => active && e.status !== 404 && setLoadError(e.message),
    );
    return () => {
      active = false;
    };
  }, [url]);

  function edit(value) {
    setMarkdown(value);
    setPreview(null);
    setSaved(null);
  }

  async function act(kind, request) {
    setBusy(kind);
    setError(null);
    try {
      await request();
    } catch (e) {
      setError(e.message);
    }
    setBusy(null);
  }

  const showPreview = () =>
    act("preview", async () =>
      setPreview(await api.post(`${url}preview/`, { markdown })),
    );

  const save = () =>
    act("save", async () => {
      const content = await api.put(url, { markdown });
      setSaved(content.state);
      setVersion((v) => v + 1);
    });

  const canSave = preview && preview.errors.length === 0 && markdown.trim();

  return (
    <Panel raised ref={panel} tabIndex={-1} aria-labelledby="conteudo-subtema">
      <Stack gap={6}>
        <h2 id="conteudo-subtema">Conteúdo de {subtopic.name}</h2>
        {loadError && (
          <StateMessage
            kind="error"
            title="Não foi possível carregar o conteúdo salvo."
          >
            {loadError}
          </StateMessage>
        )}
        <TextArea
          label="Markdown do subtema"
          help="Cole o arquivo inteiro, com o frontmatter. Depois pré-visualize para poder salvar."
          rows={14}
          value={markdown}
          onChange={(e) => edit(e.target.value)}
          spellCheck={false}
        />
        <Inline justify="between">
          <Inline>
            <Button
              variant="secondary"
              icon="file-text"
              loading={busy === "preview"}
              loadingLabel="Lendo…"
              disabled={!markdown.trim()}
              onClick={showPreview}
            >
              Pré-visualizar
            </Button>
            <Button
              icon="check"
              loading={busy === "save"}
              disabled={!canSave}
              onClick={save}
            >
              Salvar
            </Button>
          </Inline>
          <Button variant="tertiary" onClick={onClose}>
            Fechar
          </Button>
        </Inline>
        <ActionError>
          {error &&
            `Não foi possível concluir. Seu texto continua aqui. ${error}`}
        </ActionError>
        {saved && (
          <p className="ui-field__status" role="status">
            {saved === "ready"
              ? "Conteúdo salvo e pronto para estudo."
              : "Conteúdo salvo como rascunho."}
          </p>
        )}
        {preview && <Preview preview={preview} />}
        <CardApproval subtopicId={subtopic.id} version={version} />
      </Stack>
    </Panel>
  );
}

function Preview({ preview }) {
  const { state, errors, warnings, blocks, questions, cards, callouts } =
    preview;
  return (
    <Stack as="section" gap={5} aria-labelledby="previa">
      <Inline justify="between">
        <h3 id="previa">Prévia</h3>
        {state === "ready" ? (
          <Badge tone="success" icon="check-circle">
            Pronto
          </Badge>
        ) : (
          <Badge icon="file-text">Rascunho</Badge>
        )}
      </Inline>
      {state === "draft" && (
        <p className="t-meta">
          Fica pronto com uma Ideia central preenchida e ao menos uma pergunta
          com resposta de referência. Dá para salvar como rascunho assim mesmo.
        </p>
      )}
      {errors.length > 0 && (
        <StateMessage kind="error" title="Corrija antes de salvar.">
          {errors.join(" ")}
        </StateMessage>
      )}
      {warnings.length > 0 && (
        <Callout variant="info" title="Avisos">
          <ul>
            {warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </Callout>
      )}
      <PreviewList title="Blocos" empty="Nenhum bloco.">
        {blocks.map((b, i) => (
          <ListRow
            key={i}
            title={b.heading || "Texto antes do primeiro título"}
            meta={
              b.kind === "extra"
                ? "Bloco extra, mantido na posição original"
                : undefined
            }
          />
        ))}
      </PreviewList>
      <PreviewList title="Perguntas" empty="Nenhuma pergunta em Prática.">
        {questions.map((q) => (
          <ListRow
            key={q.label}
            title={`${q.label}: ${q.prompt}`}
            meta={
              q.reference_answer
                ? "Com resposta de referência"
                : "Sem resposta de referência, não conta para pronto"
            }
          />
        ))}
      </PreviewList>
      <PreviewList
        title="Cartões"
        empty="Nenhum cartão em Flashcards."
        note="Cartões novos entram pendentes; os que já existem mantêm o estado."
      >
        {cards.map((c) => (
          <ListRow
            key={c.label}
            title={`${c.label}: ${c.front}`}
            meta={c.back}
          />
        ))}
      </PreviewList>
      {callouts.map((c, i) => (
        <Callout key={i} variant="ai" source={c.source}>
          <p>{c.text.replace(/^\[!ia\]\s*/, "")}</p>
        </Callout>
      ))}
    </Stack>
  );
}

function PreviewList({ title, empty, note, children }) {
  return (
    <Stack gap={2}>
      <h4>
        {title} ({children.length})
      </h4>
      {note && <p className="t-meta">{note}</p>}
      {children.length ? (
        <List label={title}>{children}</List>
      ) : (
        <p className="t-meta">{empty}</p>
      )}
    </Stack>
  );
}

// One pending card at a time, approved or rejected with A or R; no "approve all" (spec 4.3).
function CardApproval({ subtopicId, version }) {
  const [cards, setCards] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const section = useRef(null);

  const url = `/api/flashcards/?subtopic=${subtopicId}&state=pending`;

  useEffect(() => {
    let active = true;
    api.get(url).then(
      (list) => active && setCards(list),
      (e) => active && setError(e.message),
    );
    return () => {
      active = false;
    };
  }, [url, version]);

  if (!cards)
    return error ? (
      <ActionError>{`Não foi possível carregar os cartões. ${error}`}</ActionError>
    ) : null;
  if (cards.length === 0)
    return <p className="t-meta">Nenhum cartão pendente de aprovação.</p>;

  const [card] = cards;

  async function decide(action) {
    if (busy) return;
    setBusy(true);
    try {
      await api.post(`/api/flashcards/${card.id}/${action}/`);
      setCards((list) => list.slice(1));
      setError(null);
    } catch (e) {
      setError(e.message);
      // The card may have changed elsewhere; show the list as the server has it.
      setCards(await api.get(url).catch(() => cards));
    }
    setBusy(false);
    // Keeps the shortcuts working for the next card.
    section.current?.focus();
  }

  function onKeyDown(event) {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    const action = { a: "approve", r: "reject" }[event.key.toLowerCase()];
    if (!action) return;
    event.preventDefault();
    decide(action);
  }

  return (
    <Stack
      as="section"
      gap={4}
      ref={section}
      tabIndex={-1}
      onKeyDown={onKeyDown}
      aria-labelledby="aprovar-cartoes"
      aria-describedby="aprovar-atalhos"
      className="card-approval"
    >
      <Inline justify="between">
        <h3 id="aprovar-cartoes">Aprovar cartões</h3>
        <span className="t-meta" aria-live="polite">
          {cards.length === 1 ? "1 pendente" : `${cards.length} pendentes`}
        </span>
      </Inline>
      <dl className="card-approval__card">
        <dt className="t-meta">{card.label} · Frente</dt>
        <dd>{card.front}</dd>
        <dt className="t-meta">Verso</dt>
        <dd>{card.back}</dd>
      </dl>
      <Inline>
        <Button
          icon="check"
          loading={busy}
          loadingLabel="Aprovando…"
          onClick={() => decide("approve")}
        >
          Aprovar <kbd>A</kbd>
        </Button>
        <Button
          variant="secondary"
          icon="close"
          disabled={busy}
          onClick={() => decide("reject")}
        >
          Rejeitar <kbd>R</kbd>
        </Button>
      </Inline>
      <p id="aprovar-atalhos" className="t-meta">
        Com o foco aqui, A aprova e R rejeita. O cartão aprovado entra na
        revisão como novo.
      </p>
      <ActionError>{error}</ActionError>
    </Stack>
  );
}
