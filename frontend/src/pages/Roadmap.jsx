import { useEffect, useRef, useState } from "react";

import { api } from "../api.js";
import {
  Badge,
  Button,
  Inline,
  List,
  ListRow,
  Select,
  Stack,
  StateMessage,
  StudyStatusBadge,
  Tabs,
} from "../ui/index.js";
import { useCollections } from "../useCollections.js";
import { ActionError, AddForm } from "./forms.jsx";

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

  // The title stays in place while loading or failing, so the page does not jump.
  if (error || !data) {
    return (
      <Stack gap={6}>
        <h1>Roadmap</h1>
        {error ? (
          <StateMessage
            kind="error"
            title="Não foi possível carregar o roadmap."
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
    <Stack gap={6}>
      <Inline justify="between">
        <h1>Roadmap</h1>
        <AddForm
          variant="secondary"
          label="Nome da trilha"
          button="Criar trilha"
          loadingLabel="Criando…"
          onSubmit={createTrack}
        />
      </Inline>
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
                actionError={actionError}
                onRemove={() => removeTrack(track)}
              />
            ),
          }))}
        />
      )}
    </Stack>
  );
}

function Track({ track, concepts, areaName, act, actionError, onRemove }) {
  const [conceptId, setConceptId] = useState("");
  const inTrack = new Set(track.steps.map((s) => s.concept));
  const available = concepts.filter((c) => !inTrack.has(c.id));
  const last = track.steps.length - 1;

  const conceptSelect = useRef(null);
  // Element ids to focus once the reloaded track is on screen, the first one enabled; empty
  // means the concept select. Set before the write, read when the new track renders.
  const refocus = useRef(null);

  // Moving a step re-renders the list and drops focus, so it goes back to the same button,
  // or to its sibling when the step reached the top or the bottom and the button went disabled.
  useEffect(() => {
    if (!refocus.current) return;
    const target = refocus.current.map((id) => document.getElementById(id)).find((el) => el && !el.disabled);
    refocus.current = null;
    (target ?? conceptSelect.current)?.focus();
  }, [track]);

  function move(step, direction) {
    const [same, other] = direction === "up" ? ["subir", "descer"] : ["descer", "subir"];
    refocus.current = [`${same}-${step.id}`, `${other}-${step.id}`];
    act(() => api.post(`/api/steps/${step.id}/move/`, { direction }));
  }

  function removeStep(step) {
    refocus.current = [];
    act(() => api.delete(`/api/steps/${step.id}/`));
  }

  async function addStep(event) {
    event.preventDefault();
    if (!conceptId) return;
    await act(() => api.post("/api/steps/", { track: track.id, concept: Number(conceptId) }));
    setConceptId("");
  }

  return (
    <Stack gap={5}>
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
              badges={
                <>
                  <StudyStatusBadge status={step.concept_status} />
                  {step.id === track.next_step && (
                    <Badge tone="accent" icon="arrow-right">
                      Próximo passo
                    </Badge>
                  )}
                </>
              }
              action={
                <>
                  <Button
                    id={`subir-${step.id}`}
                    variant="tertiary"
                    disabled={index === 0}
                    aria-label={`Subir ${step.concept_name}`}
                    onClick={() => move(step, "up")}
                  >
                    Subir
                  </Button>
                  <Button
                    id={`descer-${step.id}`}
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
                    aria-label={`Tirar da trilha ${step.concept_name}`}
                    onClick={() => removeStep(step)}
                  >
                    Tirar da trilha
                  </Button>
                </>
              }
            />
          ))}
        </List>
      )}
      <ActionError>{actionError && `Não foi possível concluir. ${actionError}`}</ActionError>
      {available.length > 0 && (
        <Inline as="form" align="end" className="field-row" onSubmit={addStep}>
          <Select
            ref={conceptSelect}
            label="Conceito"
            value={conceptId}
            placeholder="Escolha um conceito"
            options={available.map((c) => ({
              value: String(c.id),
              label: `${c.name} (${areaName[c.area]})`,
            }))}
            onChange={(e) => setConceptId(e.target.value)}
          />
          <Button type="submit" variant="secondary" disabled={!conceptId}>
            Adicionar à trilha
          </Button>
        </Inline>
      )}
      {concepts.length === 0 && (
        <p className="t-meta">
          Crie conceitos na <a href="#/biblioteca">Biblioteca</a> para montar a trilha.
        </p>
      )}
      <Inline justify="end">
        <Button
          variant="tertiary"
          icon="close"
          aria-label={`Remover trilha ${track.name}`}
          onClick={onRemove}
        >
          Remover trilha
        </Button>
      </Inline>
    </Stack>
  );
}
