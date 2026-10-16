import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../api.js";
import { Badge, Breadcrumb, Button, Inline, Panel, Stack, StateMessage, TextArea } from "../ui/index.js";
import CompletionSuggestion from "./CompletionSuggestion.jsx";
import { ActionError } from "./forms.jsx";
import "./practice.css";
import "./study.css";

// Practice (spec 4.8.3, DECISIONS.md D-021): one item open at a time. "Responder" starts a
// question or explanation event; the reference answer and earlier attempts appear only after
// sending; the self-assessment saves the attempt and completes the event in one request.
// The draft lives in localStorage, so closing the browser loses nothing (spec 4.8.4).

const ASSESSMENTS = [
  { value: "wrong", label: "Errei", icon: "close", tone: "neutral" },
  { value: "partial", label: "Parcial", icon: "circle", tone: "warning" },
  { value: "right", label: "Acertei", icon: "check-circle", tone: "success" },
];
const assessmentOf = (value) => ASSESSMENTS.find((a) => a.value === value);

const draftKey = (subtopicId, item) => `athenas:pratica:${subtopicId}:${item.key}`;

// Storage can be full or blocked; the screen still works, only the draft is not kept.
function readDraft(key) {
  try {
    return JSON.parse(localStorage.getItem(key)) ?? null;
  } catch {
    return null;
  }
}

function writeDraft(key, draft) {
  try {
    if (draft) localStorage.setItem(key, JSON.stringify(draft));
    else localStorage.removeItem(key);
    return true;
  } catch {
    return false;
  }
}

const time = (iso) => new Date(iso).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
const dateTime = (iso) =>
  new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });

export default function Practice({ subtopicId }) {
  const [practice, setPractice] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [openKey, setOpenKey] = useState(null);
  const [saved, setSaved] = useState(null);

  const load = useCallback(
    () => api.get(`/api/subtopics/${subtopicId}/practice/`).then(setPractice, setLoadError),
    [subtopicId],
  );

  useEffect(() => {
    load();
  }, [load]);

  if (loadError || !practice) {
    return (
      <Stack gap={6}>
        <Breadcrumb items={[{ label: "Biblioteca", href: "#/biblioteca" }, { label: "Prática" }]} />
        <h1>Prática</h1>
        {loadError?.status === 404 ? (
          <StateMessage
            title="Este subtema não foi encontrado."
            action={<Button href="#/biblioteca">Voltar à Biblioteca</Button>}
          >
            Ele pode ter sido removido. Escolha outro na Biblioteca.
          </StateMessage>
        ) : loadError ? (
          <StateMessage
            kind="error"
            title="Não foi possível carregar a prática."
            action={
              <Button
                onClick={() => {
                  setLoadError(null);
                  load();
                }}
              >
                Tentar novamente
              </Button>
            }
          >
            {loadError.message}
          </StateMessage>
        ) : (
          <p className="t-meta">Carregando…</p>
        )}
      </Stack>
    );
  }

  const items = [
    {
      key: "explicacao",
      kind: "explanation",
      title: "Explicar com minhas palavras",
      prompt: `Explique ${practice.subtopic} como se estivesse ensinando alguém.`,
      field: "Sua explicação",
      noun: "explicação",
    },
    ...practice.questions.map((q) => ({
      key: `p${q.id}`,
      kind: "question",
      question: q,
      title: q.label,
      prompt: q.prompt,
      field: "Sua resposta",
      noun: "resposta",
    })),
  ];

  function attemptsOf(item) {
    return practice.attempts.filter((a) =>
      item.kind === "question" ? a.question === item.question.id : a.kind === "explanation",
    );
  }

  function onSaved(item, attempt) {
    setPractice((p) => ({ ...p, attempts: [attempt, ...p.attempts] }));
    setOpenKey(null);
    setSaved(item.key);
  }

  return (
    <Stack gap={6}>
      <Breadcrumb
        items={[
          { label: "Biblioteca", href: "#/biblioteca" },
          { label: practice.concept, href: "#/biblioteca" },
          { label: practice.subtopic, href: `#/estudo/${subtopicId}` },
          { label: "Prática" },
        ]}
      />
      <Stack gap={6} className="study__column">
        <Stack gap={3}>
          <h1>Prática: {practice.subtopic}</h1>
          <p className="t-meta">
            Responda sem consultar o conteúdo. A resposta de referência aparece depois que você enviar.
          </p>
        </Stack>
        <Panel raised as="div" className="practice">
          <ol className="practice__list">
            {items.map((item) => (
              <PracticeItem
                key={item.key}
                item={item}
                subtopicId={subtopicId}
                attempts={attemptsOf(item)}
                open={openKey === item.key}
                justSaved={saved === item.key}
                onOpen={() => {
                  setSaved(null);
                  setOpenKey(item.key);
                }}
                onClose={() => setOpenKey(null)}
                onSaved={(attempt) => onSaved(item, attempt)}
              />
            ))}
          </ol>
          {practice.questions.length === 0 && (
            <p className="t-meta practice__note">
              Este subtema ainda não tem perguntas com resposta de referência. Elas vêm do bloco
              Prática do Markdown, em Conteúdo, na Biblioteca.
            </p>
          )}
        </Panel>
        {/* A new key per saved attempt asks the server again (DECISIONS.md D-024). */}
        {saved && <CompletionSuggestion key={practice.attempts.length} subtopicId={subtopicId} />}
      </Stack>
    </Stack>
  );
}

function PracticeItem({ item, subtopicId, attempts, open, justSaved, onOpen, onClose, onSaved }) {
  const key = draftKey(subtopicId, item);
  const [hasDraft, setHasDraft] = useState(() => readDraft(key) !== null);
  const last = attempts[0] && assessmentOf(attempts[0].self_assessment);
  const headingId = `pratica-${item.key}`;

  return (
    <li className="practice__item" aria-labelledby={headingId}>
      <Stack gap={3}>
        <h2 id={headingId} className="practice__title">
          {item.kind === "question" && <span className="practice__label">{item.title}</span>}
          {item.kind === "question" ? item.prompt : item.title}
        </h2>
        {item.kind === "explanation" && <p className="t-reading">{item.prompt}</p>}
        {open ? (
          <AnswerForm
            item={item}
            subtopicId={subtopicId}
            draftStorage={key}
            attempts={attempts}
            onDraft={setHasDraft}
            onClose={onClose}
            onSaved={onSaved}
          />
        ) : (
          <Inline justify="between">
            <Inline gap={2}>
              <p className="t-meta">
                {attempts.length === 0
                  ? "Nenhuma tentativa ainda"
                  : `${attempts.length} ${attempts.length === 1 ? "tentativa" : "tentativas"}, a última:`}
              </p>
              {last && (
                <Badge tone={last.tone} icon={last.icon}>
                  {last.label}
                </Badge>
              )}
              {hasDraft && (
                <Badge tone="info" icon="pencil">
                  Rascunho salvo
                </Badge>
              )}
            </Inline>
            <Button variant="secondary" iconEnd="arrow-right" onClick={onOpen} aria-describedby={headingId}>
              {hasDraft ? "Continuar" : "Responder"}
            </Button>
          </Inline>
        )}
        {justSaved && !open && (
          <p className="t-meta practice__saved" role="status">
            Tentativa salva.
          </p>
        )}
      </Stack>
    </li>
  );
}

function AnswerForm({ item, subtopicId, draftStorage, attempts, onDraft, onClose, onSaved }) {
  const [draft, setDraft] = useState(() => readDraft(draftStorage) ?? { text: "", submitted: false });
  const [event, setEvent] = useState(null);
  const [busy, setBusy] = useState("open");
  const [error, setError] = useState(null);
  const [storageFailed, setStorageFailed] = useState(false);
  const field = useRef(null);
  const revealed = useRef(null);

  const start = useCallback(async () => {
    setBusy("open");
    setError(null);
    try {
      const body =
        item.kind === "question"
          ? { kind: "question", question: item.question.id }
          : { kind: "explanation", subtopic: subtopicId };
      setEvent(await api.post("/api/events/", body));
    } catch (e) {
      setError(`Não foi possível começar. ${e.message}`);
    }
    setBusy(null);
  }, [item, subtopicId]);

  // One event per opening; StrictMode's second run in dev must not start another.
  const started = useRef(false);
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    start();
  }, [start]);

  useEffect(() => {
    (draft.submitted ? revealed : field).current?.focus();
  }, [draft.submitted]);

  function save(next) {
    const stored = next.text || next.submitted ? { ...next, savedAt: new Date().toISOString() } : null;
    setDraft(stored ?? next);
    setStorageFailed(!writeDraft(draftStorage, stored));
    onDraft(stored !== null);
  }

  async function assess(value) {
    setBusy(value);
    setError(null);
    try {
      const attempt = await api.post("/api/attempts/", {
        event: event.id,
        text: draft.text.trim(),
        self_assessment: value,
      });
      writeDraft(draftStorage, null);
      onDraft(false);
      onSaved(attempt);
      return;
    } catch (e) {
      setError(`Não foi possível salvar a tentativa. ${e.message}`);
    }
    setBusy(null);
  }

  const status = storageFailed
    ? "Não foi possível guardar o rascunho neste navegador."
    : draft.savedAt
      ? `Rascunho salvo às ${time(draft.savedAt)}`
      : undefined;

  if (!draft.submitted) {
    return (
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (draft.text.trim()) save({ ...draft, submitted: true });
        }}
      >
        <Stack gap={4}>
          <TextArea
            ref={field}
            label={item.field}
            rows={8}
            value={draft.text}
            status={status}
            onChange={(e) => save({ ...draft, text: e.target.value })}
          />
          <ActionError>{error}</ActionError>
          <Inline justify="between" className="study__actions">
            <Button variant="tertiary" onClick={onClose}>
              Fechar
            </Button>
            <Button type="submit" disabled={!draft.text.trim()}>
              Enviar {item.noun}
            </Button>
          </Inline>
        </Stack>
      </form>
    );
  }

  return (
    <Stack gap={5}>
      <section aria-label={item.field}>
        <p className="practice__subtitle">{item.field}</p>
        <div className="t-reading study__body">{draft.text}</div>
      </section>
      {item.kind === "question" && (
        <section className="practice__reference" aria-labelledby={`${item.key}-ref`}>
          <p id={`${item.key}-ref`} ref={revealed} tabIndex={-1} className="practice__subtitle">
            Resposta de referência
          </p>
          <div className="t-reading study__body">{item.question.reference_answer}</div>
        </section>
      )}
      {attempts.length > 0 && (
        <details className="practice__history">
          <summary>Tentativas anteriores ({attempts.length})</summary>
          <ol className="practice__attempts">
            {attempts.map((a) => {
              const { label, icon, tone } = assessmentOf(a.self_assessment);
              return (
                <li key={a.id}>
                  <Inline gap={2}>
                    <p className="t-meta">{dateTime(a.created_at)}</p>
                    <Badge tone={tone} icon={icon}>
                      {label}
                    </Badge>
                  </Inline>
                  <div className="study__body">{a.text}</div>
                </li>
              );
            })}
          </ol>
        </details>
      )}
      <fieldset className="practice__assess">
        <legend ref={item.kind === "question" ? undefined : revealed} tabIndex={-1}>
          Como foi a sua {item.noun}?
        </legend>
        <ActionError>{error}</ActionError>
        <Inline gap={3}>
          {ASSESSMENTS.map((a) => (
            <Button
              key={a.value}
              variant="secondary"
              icon={a.icon}
              loading={busy === a.value}
              disabled={!event || (busy !== null && busy !== a.value)}
              onClick={() => assess(a.value)}
            >
              {a.label}
            </Button>
          ))}
        </Inline>
        {!event && busy === null && (
          <Button variant="tertiary" onClick={start}>
            Tentar começar de novo
          </Button>
        )}
      </fieldset>
    </Stack>
  );
}
