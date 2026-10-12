import { useState } from "react";

import { api } from "../api.js";
import { Button, List, ListRow, StateMessage, Tabs } from "../ui/index.js";
import { useCollections } from "../useCollections.js";
import { NameForm, SelectField } from "./forms.jsx";

export default function Roadmap() {
  const { data, error, reload } = useCollections(["/api/tracks/", "/api/concepts/", "/api/areas/"]);
  const [selected, setSelected] = useState(null);
  const [actionError, setActionError] = useState(null);

  // Runs a write and reloads. Returns the error message, or null when it worked.
  async function run(write) {
    try {
      const result = await write();
      setActionError(null);
      await reload();
      return { result };
    } catch (e) {
      return { error: e.message };
    }
  }

  async function act(write) {
    const { error: failure } = await run(write);
    setActionError(failure ?? null);
  }

  if (error) {
    return (
      <StateMessage
        kind="error"
        title="Não foi possível carregar o roadmap."
        action={<Button onClick={reload}>Tentar novamente</Button>}
      >
        {error}
      </StateMessage>
    );
  }
  if (!data) return <p className="t-meta">Carregando…</p>;
  const [tracks, concepts, areas] = data;
  const areaName = Object.fromEntries(areas.map((a) => [a.id, a.name]));

  async function createTrack(name) {
    const { result, error: failure } = await run(() => api.post("/api/tracks/", { name }));
    if (result) setSelected(result.id);
    return failure ?? null;
  }

  async function removeTrack(track) {
    if (!window.confirm(`Remover a trilha "${track.name}"? Os conceitos continuam na biblioteca.`)) {
      return;
    }
    await act(() => api.delete(`/api/tracks/${track.id}/`));
    setSelected(null);
  }

  return (
    <>
      <h1>Roadmap</h1>
      {actionError && (
        <StateMessage kind="error" title="Não foi possível concluir.">
          {actionError}
        </StateMessage>
      )}
      {tracks.length === 0 ? (
        <StateMessage title="Nenhuma trilha ainda.">
          Uma trilha é a ordem em que você quer estudar os conceitos.
        </StateMessage>
      ) : (
        <Tabs
          label="Trilhas"
          value={selected ?? tracks[0].id}
          onChange={setSelected}
          items={tracks.map((track) => ({
            id: track.id,
            label: track.name,
            content: (
              <Track
                track={track}
                concepts={concepts}
                areaName={areaName}
                act={act}
                onRemove={() => removeTrack(track)}
              />
            ),
          }))}
        />
      )}
      <NameForm label="Nome da trilha" button="Criar trilha" onSubmit={createTrack} />
    </>
  );
}

function Track({ track, concepts, areaName, act, onRemove }) {
  const [conceptId, setConceptId] = useState("");
  const inTrack = new Set(track.steps.map((s) => s.concept));
  const available = concepts.filter((c) => !inTrack.has(c.id));
  const last = track.steps.length - 1;

  const move = (step, direction) => act(() => api.post(`/api/steps/${step.id}/move/`, { direction }));

  async function addStep(event) {
    event.preventDefault();
    if (!conceptId) return;
    await act(() => api.post("/api/steps/", { track: track.id, concept: Number(conceptId) }));
    setConceptId("");
  }

  return (
    <>
      {track.steps.length === 0 ? (
        <StateMessage title="Nenhum conceito nesta trilha.">
          Adicione um conceito abaixo. Ele pode entrar antes de ter conteúdo.
        </StateMessage>
      ) : (
        <List label={`Etapas de ${track.name}`}>
          {track.steps.map((step, index) => (
            <ListRow
              key={step.id}
              title={`${index + 1}. ${step.concept_name}`}
              meta={step.area_name}
              action={
                <>
                  <Button
                    variant="tertiary"
                    disabled={index === 0}
                    aria-label={`Subir ${step.concept_name}`}
                    onClick={() => move(step, "up")}
                  >
                    Subir
                  </Button>
                  <Button
                    variant="tertiary"
                    disabled={index === last}
                    aria-label={`Descer ${step.concept_name}`}
                    onClick={() => move(step, "down")}
                  >
                    Descer
                  </Button>
                  <Button
                    variant="tertiary"
                    icon="close"
                    onClick={() => act(() => api.delete(`/api/steps/${step.id}/`))}
                  >
                    Tirar da trilha
                  </Button>
                </>
              }
            />
          ))}
        </List>
      )}
      {available.length > 0 && (
        <form onSubmit={addStep}>
          <SelectField
            label="Conceito"
            value={conceptId}
            options={[["", "Escolha um conceito"], ...available.map((c) => [String(c.id), `${c.name} (${areaName[c.area]})`])]}
            onChange={setConceptId}
          />
          <Button type="submit" variant="secondary" disabled={!conceptId}>
            Adicionar à trilha
          </Button>
        </form>
      )}
      {concepts.length === 0 && (
        <p className="t-meta">
          Crie conceitos na <a href="#/biblioteca">Biblioteca</a> para montar a trilha.
        </p>
      )}
      <Button variant="tertiary" icon="close" onClick={onRemove}>
        Remover trilha
      </Button>
    </>
  );
}
