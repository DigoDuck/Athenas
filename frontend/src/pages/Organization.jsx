import { useState } from "react";

import { api } from "../api.js";
import { useCollections } from "../useCollections.js";
import InlineForm from "./InlineForm.jsx";

const LEVELS = [
  ["", "não definido"],
  ["iniciante", "iniciante"],
  ["intermediario", "intermediário"],
  ["avancado", "avançado"],
  ["especialista", "especialista"],
];
const DIFFICULTIES = [
  ["unset", "não definida"],
  ["easy", "fácil"],
  ["hard", "difícil"],
];
const STATUSES = [
  ["not_started", "não iniciado"],
  ["in_progress", "em andamento"],
  ["completed", "concluído"],
];

export default function Organization() {
  const { data, error, reload } = useCollections([
    "/api/areas/",
    "/api/concepts/",
    "/api/subtopics/",
  ]);
  const [actionError, setActionError] = useState(null);

  // Runs a write, reloads, and reports whether it worked.
  async function run(write) {
    try {
      await write();
      setActionError(null);
      await reload();
      return true;
    } catch (e) {
      setActionError(e.message);
      return false;
    }
  }

  async function remove(url, label) {
    if (window.confirm(`Remover "${label}"?`)) await run(() => api.delete(url));
  }

  if (error) return <p className="error">Não consegui carregar: {error}</p>;
  if (!data) return <p>Carregando…</p>;
  const [areas, concepts, subtopics] = data;

  return (
    <section>
      <h1>Organização</h1>
      {actionError && <p className="error">{actionError}</p>}
      <InlineForm
        placeholder="Nova área"
        button="Adicionar área"
        onSubmit={(name) => run(() => api.post("/api/areas/", { name }))}
      />
      {areas.length === 0 && <p className="muted">Nenhuma área ainda.</p>}
      {areas.map((area) => (
        <div key={area.id} className="area">
          <h2>
            {area.name}{" "}
            <button className="link" onClick={() => remove(`/api/areas/${area.id}/`, area.name)}>
              remover
            </button>
          </h2>
          {concepts
            .filter((c) => c.area === area.id)
            .map((concept) => (
              <Concept
                key={concept.id}
                concept={concept}
                subtopics={subtopics.filter((s) => s.concept === concept.id)}
                run={run}
                remove={remove}
              />
            ))}
          <InlineForm
            placeholder="Novo conceito"
            button="Adicionar conceito"
            onSubmit={(name) => run(() => api.post("/api/concepts/", { area: area.id, name }))}
          />
        </div>
      ))}
    </section>
  );
}

function Concept({ concept, subtopics, run, remove }) {
  return (
    <div className="concept">
      <h3>
        {concept.name}{" "}
        <button
          className="link"
          onClick={() => remove(`/api/concepts/${concept.id}/`, concept.name)}
        >
          remover
        </button>
      </h3>
      {concept.objective && <p className="muted">{concept.objective}</p>}
      {subtopics.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Subtema</th>
              <th>Nível</th>
              <th>Dificuldade percebida</th>
              <th>Status de estudo</th>
              <th>Precisa revisar</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {subtopics.map((s) => (
              <Subtopic key={s.id} subtopic={s} run={run} remove={remove} />
            ))}
          </tbody>
        </table>
      )}
      <InlineForm
        placeholder="Novo subtema"
        button="Adicionar subtema"
        onSubmit={(name) => run(() => api.post("/api/subtopics/", { concept: concept.id, name }))}
      />
    </div>
  );
}

// Each classification field is saved on its own; none is derived from another (spec 3.2).
function Subtopic({ subtopic, run, remove }) {
  const url = `/api/subtopics/${subtopic.id}/`;
  const save = (field, value) => run(() => api.patch(url, { [field]: value }));

  return (
    <tr>
      <td>{subtopic.name}</td>
      <td>
        <Select value={subtopic.level} options={LEVELS} onChange={(v) => save("level", v)} />
      </td>
      <td>
        <Select
          value={subtopic.perceived_difficulty}
          options={DIFFICULTIES}
          onChange={(v) => save("perceived_difficulty", v)}
        />
      </td>
      <td>
        <Select
          value={subtopic.study_status}
          options={STATUSES}
          onChange={(v) => save("study_status", v)}
        />
      </td>
      <td>
        <input
          type="checkbox"
          checked={subtopic.review_needed}
          onChange={(e) => save("review_needed", e.target.checked)}
          aria-label="Precisa revisar"
        />
      </td>
      <td>
        <button className="link" onClick={() => remove(url, subtopic.name)}>
          remover
        </button>
      </td>
    </tr>
  );
}

function Select({ value, options, onChange }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      {options.map(([v, label]) => (
        <option key={v} value={v}>
          {label}
        </option>
      ))}
    </select>
  );
}
