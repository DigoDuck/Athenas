import { useEffect, useRef, useState } from "react";

import { api } from "../api.js";
import {
  Button,
  Icon,
  Panel,
  Popover,
  Select,
  Stack,
  StateMessage,
  StudyStatusBadge,
} from "../ui/index.js";
import { useCollections } from "../useCollections.js";
import { ActionError, AddForm } from "./forms.jsx";
import "./home.css";
import "./roadmap.css";

export default function Roadmap({ trackId = null }) {
  const { data, error, reload } = useCollections([
    "/api/tracks/",
    "/api/concepts/",
    "/api/areas/",
    "/api/subtopics/",
  ]);
  const [selected, setSelected] = useState(trackId);
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
      <div className="scenic">
        <h1>Roadmap</h1>
        <Panel raised className="scenic__board">
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
        </Panel>
      </div>
    );
  }
  const [tracks, concepts, areas, subtopics] = data;
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

  const track = tracks.find((t) => t.id === selected) ?? tracks[0];

  return (
    <div className="scenic roadmap">
      <div className="roadmap__top">
        <div className="scenic__hero">
          <h1>Roadmap</h1>
          {track && (
            <div className="roadmap__picker">
              <label className="visually-hidden" htmlFor="roadmap-trilha">
                Trilha
              </label>
              <span className="roadmap__select">
                <select
                  id="roadmap-trilha"
                  value={track.id}
                  onChange={(e) => setSelected(Number(e.target.value))}
                >
                  {tracks.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
                <Icon name="chevron-down" />
              </span>
              <TrackMenu
                track={track}
                concepts={concepts}
                areaName={areaName}
                act={act}
                onRemove={() => removeTrack(track)}
              />
            </div>
          )}
        </div>
        <div className="roadmap__create">
          <AddForm
            variant="secondary"
            label="Nome da trilha"
            button="Criar trilha"
            loadingLabel="Criando…"
            onSubmit={createTrack}
          />
        </div>
      </div>
      {track ? (
        <Track
          key={track.id}
          track={track}
          concepts={concepts}
          subtopics={subtopics}
          act={act}
          actionError={actionError}
        />
      ) : (
        <Panel raised className="scenic__board">
          <StateMessage title="Nenhuma trilha ainda.">
            Uma trilha é a ordem em que você quer estudar os conceitos. Crie a primeira no alto da
            página.
          </StateMessage>
        </Panel>
      )}
    </div>
  );
}

// The track's own actions: add a concept to its end, or remove it.
function TrackMenu({ track, concepts, areaName, act, onRemove }) {
  const [conceptId, setConceptId] = useState("");
  const inTrack = new Set(track.steps.map((s) => s.concept));
  const available = concepts.filter((c) => !inTrack.has(c.id));

  async function addStep(event, close) {
    event.preventDefault();
    if (!conceptId) return;
    await act(() => api.post("/api/steps/", { track: track.id, concept: Number(conceptId) }));
    setConceptId("");
    close();
  }

  return (
    <Popover label={`Ações da trilha ${track.name}`} trigger={<Icon name="more-vertical" size={24} />}>
      {(close) => (
        <div className="roadmap__menu">
          {available.length > 0 ? (
            <Stack as="form" gap={3} onSubmit={(e) => addStep(e, close)}>
              <Select
                label="Adicionar conceito"
                value={conceptId}
                placeholder="Escolha um conceito"
                options={available.map((c) => ({
                  value: String(c.id),
                  label: `${c.name} (${areaName[c.area]})`,
                }))}
                onChange={(e) => setConceptId(e.target.value)}
              />
              <div>
                <Button type="submit" variant="secondary" disabled={!conceptId}>
                  Adicionar à trilha
                </Button>
              </div>
            </Stack>
          ) : (
            <p className="t-meta">
              {concepts.length === 0 ? (
                <>
                  Crie conceitos na <a href="#/biblioteca">Biblioteca</a> para montar a trilha.
                </>
              ) : (
                "Todos os conceitos já estão nesta trilha."
              )}
            </p>
          )}
          <button
            type="button"
            className="ui-popover__item ui-popover__item--danger"
            onClick={() => {
              close();
              onRemove();
            }}
          >
            <Icon name="close" />
            Remover trilha
          </button>
        </div>
      )}
    </Popover>
  );
}

function Track({ track, subtopics, act, actionError }) {
  const done = track.steps.filter((s) => s.concept_status === "completed").length;
  // Same rule as the home screen: the first subtopic of the next concept still to finish.
  const nextIndex = track.steps.findIndex((s) => s.id === track.next_step);
  const nextStep = track.steps[nextIndex];
  const nextSubtopic =
    nextStep &&
    subtopics.find((s) => s.concept === nextStep.concept && s.study_status !== "completed");
  const last = track.steps.length - 1;

  // The step whose menu button gets focus back once the reloaded track is on screen; 0 means
  // the track picker (the step left the track). Set before the write, read on the new track.
  const refocus = useRef(null);

  // Moving a step re-renders the list and drops focus, so it goes back to the same step's menu.
  useEffect(() => {
    if (refocus.current === null) return;
    const target = document.querySelector(`#etapa-${refocus.current} .ui-popover__trigger`);
    refocus.current = null;
    (target ?? document.getElementById("roadmap-trilha"))?.focus();
  }, [track]);

  function move(step, direction) {
    refocus.current = step.id;
    act(() => api.post(`/api/steps/${step.id}/move/`, { direction }));
  }

  function removeStep(step) {
    refocus.current = 0;
    act(() => api.delete(`/api/steps/${step.id}/`));
  }

  return (
    <>
      <section className="roadmap__current" aria-label="Etapa atual">
        {nextStep ? (
          <>
            <p className="scenic__eyebrow">Etapa atual · {String(nextIndex + 1).padStart(2, "0")}</p>
            <h2 className="scenic__title">{nextStep.concept_name}</h2>
            <p className="scenic__subtitle">
              {nextStep.area_name}
              {nextSubtopic && ` · ${nextSubtopic.name}`}
            </p>
            <div className="roadmap__status">
              <StudyStatusBadge status={nextStep.concept_status} />
            </div>
            <div className="scenic__action">
              {nextSubtopic ? (
                <Button
                  href={`#/estudo/${nextSubtopic.id}`}
                  iconEnd="arrow-right"
                  aria-label={`Continuar ${nextSubtopic.name}`}
                >
                  Continuar
                </Button>
              ) : (
                <Button
                  variant="secondary"
                  href="#/biblioteca"
                  aria-label={`Preparar ${nextStep.concept_name} na Biblioteca`}
                >
                  Preparar na Biblioteca
                </Button>
              )}
            </div>
          </>
        ) : (
          <>
            <h2 className="scenic__title">
              {track.steps.length === 0 ? "Trilha sem conceitos" : "Trilha concluída"}
            </h2>
            <p className="scenic__note">
              {track.steps.length === 0
                ? "Adicione o primeiro conceito pelo menu ao lado do nome da trilha. Ele pode entrar antes de ter conteúdo."
                : "Uma etapa de cada vez: todos os conceitos desta trilha foram concluídos."}
            </p>
          </>
        )}
      </section>
      {track.steps.length > 0 && (
        <Panel raised as="section" className="scenic__board" aria-labelledby="roadmap-percurso">
          <div className="roadmap__board-head">
            <h2 id="roadmap-percurso">Seu percurso</h2>
            <p className="t-meta">
              {done} de {track.steps.length}{" "}
              {track.steps.length === 1 ? "conceito concluído" : "conceitos concluídos"}
            </p>
          </div>
          <ol className="roadmap__steps">
            {track.steps.map((step, index) => (
              <li
                key={step.id}
                id={`etapa-${step.id}`}
                className="roadmap__step"
                aria-current={step === nextStep ? "step" : undefined}
              >
                <span className="roadmap__number" aria-hidden="true">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <p className="roadmap__name">{step.concept_name}</p>
                <StudyStatusBadge status={step.concept_status} />
                <Popover
                  className="roadmap__step-menu"
                  label={`Ações de ${step.concept_name}`}
                  trigger={<Icon name="more" size={24} />}
                >
                  {(close) => (
                    <>
                      <button
                        type="button"
                        className="ui-popover__item"
                        disabled={index === 0}
                        onClick={() => {
                          close();
                          move(step, "up");
                        }}
                      >
                        <Icon name="arrow-left" />
                        Mover para antes
                      </button>
                      <button
                        type="button"
                        className="ui-popover__item"
                        disabled={index === last}
                        onClick={() => {
                          close();
                          move(step, "down");
                        }}
                      >
                        <Icon name="arrow-right" />
                        Mover para depois
                      </button>
                      <button
                        type="button"
                        className="ui-popover__item ui-popover__item--danger"
                        onClick={() => {
                          close();
                          removeStep(step);
                        }}
                      >
                        <Icon name="close" />
                        Tirar da trilha
                      </button>
                    </>
                  )}
                </Popover>
              </li>
            ))}
          </ol>
          <ActionError>{actionError && `Não foi possível concluir. ${actionError}`}</ActionError>
        </Panel>
      )}
      {track.steps.length === 0 && (
        <ActionError>{actionError && `Não foi possível concluir. ${actionError}`}</ActionError>
      )}
    </>
  );
}
