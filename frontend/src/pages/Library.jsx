import { Fragment, useEffect, useRef, useState } from "react";

import { api } from "../api.js";
import {
  Button,
  Inline,
  List,
  ListRow,
  Panel,
  ReviewFlagBadge,
  Select,
  Stack,
  StateMessage,
  StudyStatusBadge,
  Switch,
} from "../ui/index.js";
import { useCollections } from "../useCollections.js";
import ContentEditor from "./ContentEditor.jsx";
import { ActionError, AddForm, toOptions } from "./forms.jsx";
import "./library.css";

const LEVELS = [
  ["", "Não definido"],
  ["iniciante", "Iniciante"],
  ["intermediario", "Intermediário"],
  ["avancado", "Avançado"],
  ["especialista", "Especialista"],
];
const DIFFICULTIES = [
  ["unset", "Não definida"],
  ["easy", "Fácil"],
  ["hard", "Difícil"],
];
const labelOf = (options, value) => options.find(([v]) => v === value)?.[1];

export default function Library() {
  const { data, error, reload } = useCollections([
    "/api/areas/",
    "/api/concepts/",
    "/api/subtopics/",
    "/api/tracks/",
  ]);
  // A failed removal shows next to the section it came from: { at: "area-1", message }.
  const [actionError, setActionError] = useState(null);
  const [editing, setEditing] = useState(null);
  const [contentOf, setContentOf] = useState(null);
  // Unsaved Markdown per subtopic id, kept while the content editor is closed.
  const [drafts, setDrafts] = useState({});

  // Runs a write and reloads. Returns the error message, or null when it worked.
  async function run(write) {
    try {
      await write();
      setActionError(null);
      await reload();
      return null;
    } catch (e) {
      return e.message;
    }
  }

  async function remove(url, question, at) {
    if (!window.confirm(question)) return;
    const message = await run(() => api.delete(url));
    setActionError(message && { at, message });
  }

  // The title stays in place while loading or failing, so the page does not jump.
  if (error || !data) {
    return (
      <Stack gap={6}>
        <h1>Biblioteca</h1>
        {error ? (
          <StateMessage
            kind="error"
            title="Não foi possível carregar a biblioteca."
            action={<Button onClick={reload}>Tentar novamente</Button>}
          >
            {error}
          </StateMessage>
        ) : (
          <p className="t-meta">Carregando…</p>
        )}
      </Stack>
    );
  }
  const [areas, concepts, subtopics, tracks] = data;

  // Closing hands focus back to the row's "Classificar" button, so keyboard users keep their place.
  function closeEditor() {
    const id = editing;
    setEditing(null);
    document.getElementById(`classificar-${id}`)?.focus();
  }

  // Saving can change the level (frontmatter `nivel`), so the list reloads on close.
  function closeContent() {
    const id = contentOf;
    setContentOf(null);
    reload();
    document.getElementById(`conteudo-${id}`)?.focus();
  }

  return (
    <Stack gap={6}>
      <Inline justify="between">
        <h1>Biblioteca</h1>
        <AddForm
          variant="secondary"
          label="Nome da área"
          button="Adicionar área"
          onSubmit={(name) => run(() => api.post("/api/areas/", { name }))}
        />
      </Inline>
      {areas.length === 0 && (
        <StateMessage title="Seu primeiro conceito começa aqui.">
          Crie uma área, como Programação ou Inglês, e depois os conceitos dela.
        </StateMessage>
      )}
      {areas.map((area) => {
        const areaConcepts = concepts.filter((c) => c.area === area.id);
        return (
          <Panel key={area.id} aria-labelledby={`area-${area.id}`}>
            <Inline justify="between">
              <h2 id={`area-${area.id}`}>{area.name}</h2>
              {/* The API refuses to remove an area that still has concepts, so say why instead. */}
              {areaConcepts.length === 0 ? (
                <Button
                  variant="tertiary"
                  icon="close"
                  aria-label={`Remover área ${area.name}`}
                  onClick={() =>
                    remove(`/api/areas/${area.id}/`, `Remover a área "${area.name}"?`, `area-${area.id}`)
                  }
                >
                  Remover área
                </Button>
              ) : (
                <p className="t-meta">Para remover a área, remova antes os conceitos dela.</p>
              )}
            </Inline>
            <ActionError>{removeFailure(actionError, `area-${area.id}`)}</ActionError>
            {areaConcepts.map((concept) => (
              <Concept
                key={concept.id}
                concept={concept}
                subtopics={subtopics.filter((s) => s.concept === concept.id)}
                trackCount={tracks.filter((t) => t.steps.some((s) => s.concept === concept.id)).length}
                editing={editing}
                onEdit={setEditing}
                onCloseEditor={closeEditor}
                contentOf={contentOf}
                onContent={setContentOf}
                onCloseContent={closeContent}
                drafts={drafts}
                onDraft={(id, text) => setDrafts((all) => ({ ...all, [id]: text }))}
                run={run}
                remove={remove}
                actionError={actionError}
              />
            ))}
            <AddForm
              label="Nome do conceito"
              button="Adicionar conceito"
              onSubmit={(name) => run(() => api.post("/api/concepts/", { area: area.id, name }))}
            />
          </Panel>
        );
      })}
    </Stack>
  );
}

// Level and difficulty as row metadata, only the ones already set ("Não definido" is noise).
function classification(subtopic) {
  const parts = [];
  if (subtopic.level) parts.push(`Nível: ${labelOf(LEVELS, subtopic.level)}`);
  if (subtopic.perceived_difficulty !== "unset") {
    parts.push(`Dificuldade: ${labelOf(DIFFICULTIES, subtopic.perceived_difficulty)}`);
  }
  return parts.join(" · ") || undefined;
}

// The removal error message for one section, or false when it failed somewhere else.
const removeFailure = (error, at) => error?.at === at && `Não foi possível remover. ${error.message}`;

function Concept({
  concept,
  subtopics,
  trackCount,
  editing,
  onEdit,
  onCloseEditor,
  contentOf,
  onContent,
  onCloseContent,
  drafts,
  onDraft,
  run,
  remove,
  actionError,
}) {
  const at = `concept-${concept.id}`;
  // Removing a concept also removes it from every track (steps cascade), so the question says so.
  const question =
    `Remover o conceito "${concept.name}"?` +
    (trackCount ? ` Ele também sai de ${trackCount === 1 ? "1 trilha" : `${trackCount} trilhas`}.` : "");

  return (
    <Stack as="section" gap={3} className="library-concept" aria-labelledby={`concept-${concept.id}`}>
      <Inline justify="between">
        <Inline gap={3}>
          <h3 id={`concept-${concept.id}`} className="t-subsection-title">
            {concept.name}
          </h3>
          {/* Derived from the subtopics, never set by hand (spec 4.4.6). */}
          <StudyStatusBadge status={concept.study_status} />
        </Inline>
        {/* The API refuses to remove a concept that still has subtopics, so say why instead. */}
        {subtopics.length === 0 ? (
          <Button
            variant="tertiary"
            icon="close"
            aria-label={`Remover conceito ${concept.name}`}
            onClick={() => remove(`/api/concepts/${concept.id}/`, question, at)}
          >
            Remover conceito
          </Button>
        ) : (
          <p className="t-meta">Para remover o conceito, remova antes os subtemas dele.</p>
        )}
      </Inline>
      {concept.objective && <p className="t-meta">{concept.objective}</p>}
      {subtopics.length > 0 && (
        <List label={`Subtemas de ${concept.name}`}>
          {subtopics.map((s) => (
            <Fragment key={s.id}>
              <ListRow
                title={s.name}
                meta={classification(s)}
                badges={
                  <>
                    <StudyStatusBadge status={s.study_status} />
                    {s.review_needed && <ReviewFlagBadge />}
                  </>
                }
                action={
                  <>
                    <Button
                      variant="tertiary"
                      iconEnd="arrow-right"
                      href={`#/estudo/${s.id}`}
                      aria-label={`Estudar ${s.name}`}
                    >
                      Estudar
                    </Button>
                    <Button
                      variant="tertiary"
                      iconEnd="arrow-right"
                      href={`#/pratica/${s.id}`}
                      aria-label={`Praticar ${s.name}`}
                    >
                      Praticar
                    </Button>
                    <Button
                      id={`conteudo-${s.id}`}
                      variant="tertiary"
                      icon="file-text"
                      aria-label={`Conteúdo de ${s.name}`}
                      aria-pressed={contentOf === s.id}
                      onClick={() => onContent(contentOf === s.id ? null : s.id)}
                    >
                      Conteúdo
                    </Button>
                    <Button
                      id={`classificar-${s.id}`}
                      variant="tertiary"
                      icon="pencil"
                      aria-label={`Classificar ${s.name}`}
                      aria-pressed={editing === s.id}
                      onClick={() => onEdit(editing === s.id ? null : s.id)}
                    >
                      Classificar
                    </Button>
                    <Button
                      variant="tertiary"
                      icon="close"
                      aria-label={`Remover ${s.name}`}
                      onClick={() => remove(`/api/subtopics/${s.id}/`, `Remover o subtema "${s.name}"?`, at)}
                    >
                      Remover
                    </Button>
                  </>
                }
              />
              {/* Editors open right under their row, not at the end of the page. */}
              {editing === s.id && <SubtopicEditor subtopic={s} run={run} onClose={onCloseEditor} />}
              {contentOf === s.id && (
                <ContentEditor
                  subtopic={s}
                  draft={drafts[s.id]}
                  onDraft={(text) => onDraft(s.id, text)}
                  onClose={onCloseContent}
                />
              )}
            </Fragment>
          ))}
        </List>
      )}
      <ActionError>{removeFailure(actionError, at)}</ActionError>
      <AddForm
        label="Nome do subtema"
        button="Adicionar subtema"
        onSubmit={(name) => run(() => api.post("/api/subtopics/", { concept: concept.id, name }))}
      />
    </Stack>
  );
}

// Each classification field is saved on its own; none is derived from another (spec 3.2).
function SubtopicEditor({ subtopic, run, onClose }) {
  const [error, setError] = useState(null);
  const url = `/api/subtopics/${subtopic.id}/`;
  const save = async (field, value) => setError(await run(() => api.patch(url, { [field]: value })));
  const reopen = async () => setError(await run(() => api.post(`${url}reopen/`)));

  // Focus moves into the editor, so keyboard and screen reader users land on it.
  const panel = useRef(null);
  useEffect(() => panel.current?.focus(), []);

  return (
    <li
      className="library-drawer"
      ref={panel}
      tabIndex={-1}
      aria-labelledby="classificar-subtema"
      onKeyDown={(e) => e.key === "Escape" && onClose()}
    >
      <h4 id="classificar-subtema">Classificar {subtopic.name}</h4>
      {error && (
        <StateMessage kind="error" title="Não foi possível salvar.">
          {error}
        </StateMessage>
      )}
      <Inline gap={4} align="start" className="field-row">
        <Select
          label="Nível"
          value={subtopic.level}
          options={toOptions(LEVELS)}
          onChange={(e) => save("level", e.target.value)}
        />
        <Select
          label="Dificuldade percebida"
          value={subtopic.perceived_difficulty}
          options={toOptions(DIFFICULTIES)}
          onChange={(e) => save("perceived_difficulty", e.target.value)}
        />
      </Inline>
      {/* Study status follows the rules of spec 4.4; only a completion can be undone (D-024). */}
      <div className="ui-field">
        <p className="ui-field__label">Status de estudo</p>
        <Inline gap={3}>
          <StudyStatusBadge status={subtopic.study_status} />
          {subtopic.study_status === "completed" && (
            <Button variant="secondary" onClick={reopen}>
              Reabrir subtema
            </Button>
          )}
        </Inline>
        <p className="ui-field__help">
          Muda sozinho ao abrir o primeiro bloco e quando você confirma a conclusão sugerida.
        </p>
      </div>
      <Switch
        label="Marcado para revisar"
        checked={subtopic.review_needed}
        onChange={(v) => save("review_needed", v)}
      />
      <Inline justify="between">
        <p className="t-meta">Cada campo é salvo assim que muda.</p>
        <Button variant="secondary" onClick={onClose}>
          Fechar
        </Button>
      </Inline>
    </li>
  );
}
