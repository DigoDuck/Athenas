import { useState } from "react";

import { api } from "../api.js";
import { useCollections } from "../useCollections.js";
import InlineForm from "./InlineForm.jsx";

export default function Roadmap() {
  const { data, error, reload } = useCollections(["/api/tracks/", "/api/concepts/", "/api/areas/"]);
  const [selected, setSelected] = useState(null);
  const [actionError, setActionError] = useState(null);

  async function run(write) {
    try {
      const result = await write();
      setActionError(null);
      await reload();
      return result ?? true;
    } catch (e) {
      setActionError(e.message);
      return false;
    }
  }

  if (error) return <p className="error">Não consegui carregar: {error}</p>;
  if (!data) return <p>Carregando…</p>;
  const [tracks, concepts, areas] = data;
  const track = tracks.find((t) => t.id === selected) ?? tracks[0];
  const areaName = Object.fromEntries(areas.map((a) => [a.id, a.name]));

  async function createTrack(name) {
    const created = await run(() => api.post("/api/tracks/", { name }));
    if (created) setSelected(created.id);
    return Boolean(created);
  }

  async function removeTrack() {
    if (!window.confirm(`Remover a trilha "${track.name}"? Os conceitos continuam existindo.`)) {
      return;
    }
    await run(() => api.delete(`/api/tracks/${track.id}/`));
    setSelected(null);
  }

  return (
    <section>
      <h1>Roadmap</h1>
      {actionError && <p className="error">{actionError}</p>}
      <div className="tracks">
        {tracks.map((t) => (
          <button
            key={t.id}
            className={t.id === track?.id ? "tab active" : "tab"}
            onClick={() => setSelected(t.id)}
          >
            {t.name}
          </button>
        ))}
        <InlineForm placeholder="Nova trilha" button="Criar trilha" onSubmit={createTrack} />
      </div>

      {!track && <p className="muted">Nenhuma trilha ainda.</p>}
      {track && (
        <Track
          track={track}
          concepts={concepts}
          areaName={areaName}
          run={run}
          onRemove={removeTrack}
        />
      )}
    </section>
  );
}

function Track({ track, concepts, areaName, run, onRemove }) {
  const [conceptId, setConceptId] = useState("");
  const inTrack = new Set(track.steps.map((s) => s.concept));
  const available = concepts.filter((c) => !inTrack.has(c.id));
  const last = track.steps.length - 1;

  const move = (step, direction) => run(() => api.post(`/api/steps/${step.id}/move/`, { direction }));

  async function addStep(event) {
    event.preventDefault();
    if (!conceptId) return;
    const ok = await run(() =>
      api.post("/api/steps/", { track: track.id, concept: Number(conceptId) }),
    );
    if (ok) setConceptId("");
  }

  return (
    <div>
      <h2>
        {track.name}{" "}
        <button className="link" onClick={onRemove}>
          remover trilha
        </button>
      </h2>
      {track.steps.length === 0 && <p className="muted">Nenhum conceito nesta trilha.</p>}
      <ol className="steps">
        {track.steps.map((step, index) => (
          <li key={step.id}>
            <span className="step-name">
              {step.concept_name} <span className="muted">· {step.area_name}</span>
            </span>
            <span className="step-actions">
              <button
                onClick={() => move(step, "up")}
                disabled={index === 0}
                aria-label="Mover para cima"
              >
                ↑
              </button>
              <button
                onClick={() => move(step, "down")}
                disabled={index === last}
                aria-label="Mover para baixo"
              >
                ↓
              </button>
              <button className="link" onClick={() => run(() => api.delete(`/api/steps/${step.id}/`))}>
                tirar da trilha
              </button>
            </span>
          </li>
        ))}
      </ol>
      {available.length > 0 && (
        <form className="inline-form" onSubmit={addStep}>
          <select value={conceptId} onChange={(e) => setConceptId(e.target.value)}>
            <option value="">Escolha um conceito</option>
            {available.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({areaName[c.area]})
              </option>
            ))}
          </select>
          <button type="submit">Adicionar à trilha</button>
        </form>
      )}
      {concepts.length === 0 && (
        <p className="muted">
          Crie conceitos em <a href="#/organizacao">Organização</a> para montar a trilha.
        </p>
      )}
    </div>
  );
}
