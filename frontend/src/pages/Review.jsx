import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../api.js";
import { Button, Icon, Inline, Panel, Select, Stack, StateMessage, TextArea } from "../ui/index.js";
import { ActionError, toOptions } from "./forms.jsx";
import "./review.css";
import "./study.css";

// Review (spec 4.6, DECISIONS.md D-025): today's queue one card at a time. Showing a card starts
// a review event; the rating saves the review and completes that event in one request. After
// each rating the queue is asked again, so a failed card returns when Py-FSRS says it is due.

const RATINGS = [
  { value: "again", label: "Errei", icon: "close", key: "1" },
  { value: "hard", label: "Parcial", icon: "circle", key: "2" },
  { value: "good", label: "Acertei", icon: "check-circle", key: "3" },
];

export default function Review() {
  const [queue, setQueue] = useState(null);
  const [loadError, setLoadError] = useState(null);
  // Counts ratings, so a card shown again after a rating is a new showing with a new event.
  const [round, setRound] = useState(0);
  const [creating, setCreating] = useState(false);

  const load = useCallback(
    () =>
      api.get("/api/reviews/today/").then(
        (data) => {
          setQueue(data);
          setLoadError(null);
        },
        setLoadError,
      ),
    [],
  );

  useEffect(() => {
    load();
  }, [load]);

  async function onRated() {
    await load();
    setRound((n) => n + 1);
  }

  const [card] = queue?.cards ?? [];

  return (
    <div className="reviews">
      <header className="reviews__head">
        <Stack gap={2}>
          <h1>Revisões</h1>
          {queue && <p className="t-meta">Revisões de hoje: {queue.count}</p>}
        </Stack>
        <Button
          variant="secondary"
          icon={creating ? "close" : "plus"}
          aria-expanded={creating}
          aria-controls={creating ? "novo-cartao-form" : undefined}
          onClick={() => setCreating(!creating)}
        >
          {creating ? "Fechar novo cartão" : "Novo cartão"}
        </Button>
      </header>
      {/* Reloading under a card on screen could swap it for the new one and abandon its event. */}
      {creating && <ManualCardForm onCreated={() => !card && load()} />}
      {loadError ? (
        <StateMessage
          kind="error"
          title="Não foi possível carregar as revisões."
          action={<Button onClick={load}>Tentar novamente</Button>}
        >
          {loadError.message}
        </StateMessage>
      ) : !queue ? (
        <p className="t-meta">Carregando…</p>
      ) : card ? (
        <ReviewCard key={`${card.id}:${round}`} card={card} focusOnShow={round > 0} onRated={onRated} />
      ) : (
        <Panel raised as="div" className="reviews__empty">
          <Icon name="cards" size={56} />
          <p className="ui-state__title">Nenhum cartão para revisar agora.</p>
          <p className="ui-state__text">Os próximos aparecem aqui quando chegar a hora de revê-los.</p>
          <Inline gap={5} justify="center" className="reviews__empty-actions">
            <Button href="#/inicio" iconEnd="arrow-right">
              Voltar ao estudo
            </Button>
            <Button variant="secondary" icon="refresh" onClick={load}>
              Procurar de novo
            </Button>
          </Inline>
        </Panel>
      )}
      <aside className="reviews__note" aria-label="Sobre os cartões">
        <Icon name="info" size={32} />
        <div>
          <p>Cartões importados só entram na revisão após aprovação.</p>
          <p className="t-meta">Cartões manuais criados aqui entram diretamente na revisão.</p>
        </div>
        <a href="#/biblioteca" className="reviews__note-link">
          Conferir na Biblioteca
          <Icon name="arrow-right" />
        </a>
      </aside>
    </div>
  );
}

function ReviewCard({ card, focusOnShow, onRated }) {
  const [event, setEvent] = useState(null);
  const [revealed, setRevealed] = useState(false);
  const [busy, setBusy] = useState("open");
  const [error, setError] = useState(null);
  const front = useRef(null);
  const back = useRef(null);

  const start = useCallback(async () => {
    setBusy("open");
    setError(null);
    try {
      setEvent(await api.post("/api/events/", { kind: "review_session" }));
    } catch (e) {
      setError(`Não foi possível começar a revisão. ${e.message}`);
    }
    setBusy(null);
  }, []);

  // One event per showing; StrictMode's second run in dev must not start another.
  const started = useRef(false);
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    start();
    if (focusOnShow) front.current?.focus();
  }, [start, focusOnShow]);

  useEffect(() => {
    if (revealed) back.current?.focus();
  }, [revealed]);

  const rate = useCallback(
    async (rating) => {
      if (!event || busy !== null) return;
      setBusy(rating);
      setError(null);
      try {
        await api.post("/api/reviews/", { event: event.id, flashcard: card.id, rating });
        await onRated();
        return;
      } catch (e) {
        setError(`Não foi possível salvar a avaliação. ${e.message}`);
      }
      setBusy(null);
    },
    [event, busy, card.id, onRated],
  );

  // Shortcuts work anywhere on the screen except while typing in a field (D-025).
  useEffect(() => {
    function onKeyDown(e) {
      if (e.altKey || e.ctrlKey || e.metaKey || e.repeat) return;
      if (e.target.closest?.("input, textarea, select, [contenteditable]")) return;
      if (!revealed) {
        // A focused button or link keeps its own Space and Enter.
        if ((e.key === " " || e.key === "Enter") && !e.target.closest?.("button, a")) {
          e.preventDefault();
          setRevealed(true);
        }
        return;
      }
      const choice = RATINGS.find((r) => r.key === e.key);
      if (choice) {
        e.preventDefault();
        rate(choice.value);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [revealed, rate]);

  return (
    <Panel raised as="section" className="review" aria-label="Cartão">
      <Stack gap={5}>
        <div>
          <p className="review__label">Pergunta</p>
          <p ref={front} tabIndex={-1} className="t-reading study__text">
            {card.front}
          </p>
        </div>
        {revealed ? (
          <>
            <div className="review__back">
              <p ref={back} tabIndex={-1} className="review__label">
                Resposta
              </p>
              <p className="t-reading study__text">
                {card.back}
              </p>
            </div>
            <fieldset className="review__assess">
              <legend>Como foi?</legend>
              <Inline gap={3}>
                {RATINGS.map((r) => (
                  <Button
                    key={r.value}
                    variant="secondary"
                    icon={r.icon}
                    loading={busy === r.value}
                    disabled={!event || (busy !== null && busy !== r.value)}
                    onClick={() => rate(r.value)}
                  >
                    {r.label} <kbd>{r.key}</kbd>
                  </Button>
                ))}
              </Inline>
            </fieldset>
          </>
        ) : (
          <div className="review__assess">
            <Button onClick={() => setRevealed(true)}>
              Mostrar resposta <kbd>Espaço</kbd>
            </Button>
          </div>
        )}
        <ActionError>{error}</ActionError>
        {!event && busy === null && (
          <Inline>
            <Button variant="tertiary" onClick={start}>
              Tentar começar de novo
            </Button>
          </Inline>
        )}
        <p className="t-meta">
          Espaço ou Enter mostra a resposta. Depois, 1 errei, 2 parcial e 3 acertei.
        </p>
      </Stack>
    </Panel>
  );
}

// A manual card goes on a subtopic, or on the concept when no subtopic is chosen (spec Q6).
function ManualCardForm({ onCreated }) {
  const [lists, setLists] = useState(null);
  const [listError, setListError] = useState(null);
  const [concept, setConcept] = useState("");
  const [subtopic, setSubtopic] = useState("");
  const [front, setFront] = useState("");
  const [back, setBack] = useState("");
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [created, setCreated] = useState(false);

  const loadLists = useCallback(
    () =>
      Promise.all(["/api/areas/", "/api/concepts/", "/api/subtopics/"].map((url) => api.get(url))).then(
        (data) => {
          setLists(data);
          setListError(null);
        },
        (e) => setListError(e.message),
      ),
    [],
  );

  useEffect(() => {
    loadLists();
  }, [loadLists]);

  if (!lists) {
    return listError ? <ActionError>{`Não foi possível carregar os conceitos. ${listError}`}</ActionError> : null;
  }

  const [areas, concepts, subtopics] = lists;
  const areaName = Object.fromEntries(areas.map((a) => [a.id, a.name]));
  const conceptOptions = toOptions(concepts.map((c) => [c.id, `${c.name} (${areaName[c.area]})`]));
  const subtopicOptions = toOptions(
    subtopics.filter((s) => String(s.concept) === concept).map((s) => [s.id, s.name]),
  );

  async function submit(e) {
    e.preventDefault();
    const missing = {
      concept: !concept && "Escolha um conceito.",
      front: !front.trim() && "Escreva a frente do cartão.",
      back: !back.trim() && "Escreva o verso do cartão.",
    };
    setErrors(missing);
    setCreated(false);
    if (Object.values(missing).some(Boolean)) return;
    setSaving(true);
    try {
      const where = subtopic ? { subtopic: Number(subtopic) } : { concept: Number(concept) };
      await api.post("/api/flashcards/", { ...where, front: front.trim(), back: back.trim() });
      setFront("");
      setBack("");
      setCreated(true);
      onCreated();
    } catch (error) {
      setErrors({ form: `Não foi possível criar o cartão. ${error.message}` });
    }
    setSaving(false);
  }

  return (
    <Panel as="section" className="review" id="novo-cartao-form" aria-labelledby="novo-cartao">
      <Stack as="form" gap={4} onSubmit={submit} noValidate>
        <Stack gap={2}>
          <h2 id="novo-cartao">Novo cartão</h2>
          <p className="t-meta">
            Cartões criados aqui entram direto na revisão, sem aprovação, e começam como novos.
          </p>
        </Stack>
        {concepts.length === 0 ? (
          <p className="t-meta">Cadastre um conceito na Biblioteca para criar cartões.</p>
        ) : (
          <>
            <Inline gap={4} align="start" className="review__where">
              <Select
                label="Conceito"
                required
                placeholder="Escolha um conceito"
                options={conceptOptions}
                value={concept}
                error={errors.concept || undefined}
                onChange={(e) => {
                  setConcept(e.target.value);
                  setSubtopic("");
                }}
              />
              <Select
                label="Subtema"
                help="Opcional. Sem subtema, o cartão fica no conceito."
                placeholder="Só o conceito"
                options={subtopicOptions}
                value={subtopic}
                disabled={!concept || subtopicOptions.length === 0}
                onChange={(e) => setSubtopic(e.target.value)}
              />
            </Inline>
            <TextArea
              label="Frente"
              required
              rows={3}
              value={front}
              error={errors.front || undefined}
              onChange={(e) => setFront(e.target.value)}
            />
            <TextArea
              label="Verso"
              required
              rows={4}
              value={back}
              error={errors.back || undefined}
              onChange={(e) => setBack(e.target.value)}
            />
            <ActionError>{errors.form}</ActionError>
            <Inline justify="between">
              <p className="t-meta review__created" role="status">
                {created ? "Cartão criado." : ""}
              </p>
              <Button type="submit" variant="secondary" loading={saving} loadingLabel="Criando…">
                Criar cartão
              </Button>
            </Inline>
          </>
        )}
      </Stack>
    </Panel>
  );
}
