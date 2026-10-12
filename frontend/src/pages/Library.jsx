import { useState } from "react";

import { api } from "../api.js";
import {
  Button,
  List,
  ListRow,
  Panel,
  ReviewFlagBadge,
  StateMessage,
  StudyStatusBadge,
  Switch,
  Tag,
} from "../ui/index.js";
import { useCollections } from "../useCollections.js";
import { NameForm, SelectField } from "./forms.jsx";

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
const STATUSES = [
  ["not_started", "Não iniciado"],
  ["in_progress", "Em andamento"],
  ["completed", "Concluído"],
];
const labelOf = (options, value) => options.find(([v]) => v === value)?.[1];

export default function Library() {
  const { data, error, reload } = useCollections([
    "/api/areas/",
    "/api/concepts/",
    "/api/subtopics/",
  ]);
  const [actionError, setActionError] = useState(null);
  const [editing, setEditing] = useState(null);

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

  async function remove(url, label) {
    if (!window.confirm(`Remover "${label}"?`)) return;
    setActionError(await run(() => api.delete(url)));
  }

  if (error) {
    return (
      <StateMessage
        kind="error"
        title="Não foi possível carregar a biblioteca."
        action={<Button onClick={reload}>Tentar novamente</Button>}
      >
        {error}
      </StateMessage>
    );
  }
  if (!data) return <p className="t-meta">Carregando…</p>;
  const [areas, concepts, subtopics] = data;
  const editingSubtopic = subtopics.find((s) => s.id === editing);

  return (
    <>
      <h1>Biblioteca</h1>
      {actionError && (
        <StateMessage kind="error" title="Não foi possível remover.">
          {actionError}
        </StateMessage>
      )}
      {areas.length === 0 && (
        <StateMessage title="Seu primeiro conceito começa aqui.">
          Crie uma área, como Programação ou Inglês, e depois os conceitos dela.
        </StateMessage>
      )}
      {areas.map((area) => (
        <Panel key={area.id} aria-labelledby={`area-${area.id}`}>
          <h2 id={`area-${area.id}`}>{area.name}</h2>
          <Button
            variant="tertiary"
            icon="close"
            onClick={() => remove(`/api/areas/${area.id}/`, area.name)}
          >
            Remover área
          </Button>
          {concepts
            .filter((c) => c.area === area.id)
            .map((concept) => (
              <Concept
                key={concept.id}
                concept={concept}
                subtopics={subtopics.filter((s) => s.concept === concept.id)}
                editing={editing}
                onEdit={setEditing}
                run={run}
                remove={remove}
              />
            ))}
          <NameForm
            label="Nome do conceito"
            button="Adicionar conceito"
            onSubmit={(name) => run(() => api.post("/api/concepts/", { area: area.id, name }))}
          />
        </Panel>
      ))}
      {editingSubtopic && (
        <SubtopicEditor
          subtopic={editingSubtopic}
          run={run}
          onClose={() => setEditing(null)}
        />
      )}
      <NameForm
        label="Nome da área"
        button="Adicionar área"
        onSubmit={(name) => run(() => api.post("/api/areas/", { name }))}
      />
    </>
  );
}

function Concept({ concept, subtopics, editing, onEdit, run, remove }) {
  return (
    <section aria-labelledby={`concept-${concept.id}`}>
      <h3 id={`concept-${concept.id}`}>{concept.name}</h3>
      {concept.objective && <p className="t-meta">{concept.objective}</p>}
      <Button
        variant="tertiary"
        icon="close"
        onClick={() => remove(`/api/concepts/${concept.id}/`, concept.name)}
      >
        Remover conceito
      </Button>
      {subtopics.length > 0 && (
        <List label={`Subtemas de ${concept.name}`}>
          {subtopics.map((s) => (
            <ListRow
              key={s.id}
              title={s.name}
              meta={`Nível: ${labelOf(LEVELS, s.level)} · Dificuldade: ${labelOf(DIFFICULTIES, s.perceived_difficulty)}`}
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
                    icon="pencil"
                    aria-pressed={editing === s.id}
                    onClick={() => onEdit(editing === s.id ? null : s.id)}
                  >
                    Classificar
                  </Button>
                  <Button
                    variant="tertiary"
                    icon="close"
                    onClick={() => remove(`/api/subtopics/${s.id}/`, s.name)}
                  >
                    Remover
                  </Button>
                </>
              }
            />
          ))}
        </List>
      )}
      <NameForm
        label="Nome do subtema"
        button="Adicionar subtema"
        onSubmit={(name) => run(() => api.post("/api/subtopics/", { concept: concept.id, name }))}
      />
    </section>
  );
}

// Each classification field is saved on its own; none is derived from another (spec 3.2).
function SubtopicEditor({ subtopic, run, onClose }) {
  const [error, setError] = useState(null);
  const url = `/api/subtopics/${subtopic.id}/`;
  const save = async (field, value) => setError(await run(() => api.patch(url, { [field]: value })));

  return (
    <Panel raised aria-labelledby="classificar-subtema">
      <h2 id="classificar-subtema">Classificar {subtopic.name}</h2>
      {error && (
        <StateMessage kind="error" title="Não foi possível salvar.">
          {error}
        </StateMessage>
      )}
      <SelectField
        label="Nível"
        value={subtopic.level}
        options={LEVELS}
        onChange={(v) => save("level", v)}
      />
      <SelectField
        label="Dificuldade percebida"
        value={subtopic.perceived_difficulty}
        options={DIFFICULTIES}
        onChange={(v) => save("perceived_difficulty", v)}
      />
      <SelectField
        label="Status de estudo"
        value={subtopic.study_status}
        options={STATUSES}
        onChange={(v) => save("study_status", v)}
      />
      <Switch
        label="Marcado para revisar"
        checked={subtopic.review_needed}
        onChange={(v) => save("review_needed", v)}
      />
      <Tag>Cada campo é salvo assim que muda.</Tag>
      <Button variant="secondary" onClick={onClose}>
        Fechar
      </Button>
    </Panel>
  );
}
