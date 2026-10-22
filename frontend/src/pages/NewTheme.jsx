import { useEffect, useRef, useState } from "react";

import { api } from "../api.js";
import {
  Badge,
  Button,
  Callout,
  GeneratedByBadge,
  Inline,
  List,
  Panel,
  Select,
  Stack,
  StateMessage,
  TextArea,
  TextField,
} from "../ui/index.js";
import { useCollections } from "../useCollections.js";
import { ActionError } from "./forms.jsx";
import { buildCorrection, buildRequest, LEVELS } from "./themeRequest.js";
import "./newTheme.css";

// "Novo tema" (DECISIONS.md D-040): the app writes the request for any chat AI, Diogo pastes the
// answer back, the parser checks it, and one round creates one concept's subtopics with their
// cards pending. Calling an AI from the app stays out of v1 (D-030).

// The form survives closing the browser for the next round, and the pasted answer until its round
// is created, like the practice draft.
const DRAFT_KEY = "athenas:novo-tema";
const EMPTY = { theme: "", goal: "", area: "", track: "", level: "iniciante", origin: "", answer: "" };
const AIS = ["claude", "gemini", "chatgpt"];

const ACTIONS = {
  create: "Novo subtema",
  fill: "Preenche um subtema vazio",
  same: "Já está no app, igual",
  keep: "Já tem outro texto, fica como está",
};

function loadDraft() {
  try {
    const saved = JSON.parse(localStorage.getItem(DRAFT_KEY)) ?? {};
    // Only the known text fields: an old or hand-edited draft never breaks the screen.
    const known = Object.entries(saved).filter(([k, v]) => k in EMPTY && typeof v === "string");
    const draft = { ...EMPTY, ...Object.fromEntries(known) };
    return LEVELS.some(([value]) => value === draft.level) ? draft : { ...draft, level: EMPTY.level };
  } catch {
    return EMPTY;
  }
}

const sameName = (a, b) => a.toLowerCase() === b.trim().toLowerCase();
// A focused element that unmounts leaves the focus on the body.
const focusLost = () => !document.activeElement || document.activeElement === document.body;

export default function NewTheme() {
  const { data, error, reload } = useCollections(["/api/areas/", "/api/tracks/", "/api/concepts/"]);
  const [form, setForm] = useState(loadDraft);
  // The check of the exact text in the field: saving needs one, so nothing is created unseen.
  const [report, setReport] = useState(null);
  const [created, setCreated] = useState(null);
  const [busy, setBusy] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [copied, setCopied] = useState(null);
  const [missing, setMissing] = useState(null);
  const [reloading, setReloading] = useState(false);
  const copyButton = useRef(null);
  const checkButton = useRef(null);
  const createdMessage = useRef(null);
  const retryButton = useRef(null);
  // Where the keyboard goes once a save ends: the button it was on leaves with the check.
  const refocus = useRef(null);

  useEffect(() => {
    try {
      localStorage.setItem(DRAFT_KEY, JSON.stringify(form));
    } catch {
      // Storage full or blocked: the screen still works, the draft just does not survive.
    }
  }, [form]);

  useEffect(() => {
    if (busy !== null || !refocus.current) return;
    if (focusLost()) refocus.current.current?.focus();
    refocus.current = null;
  }, [busy]);

  if (!data) {
    return (
      <Stack gap={6}>
        <h1>Novo tema</h1>
        {error ? (
          <StateMessage
            kind="error"
            title="Não foi possível carregar áreas e trilhas."
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
  const [areas, tracks, allConcepts] = data;
  // The backend matches names ignoring case, so the screen does too.
  const area = areas.find((a) => sameName(a.name, form.area));
  const track = tracks.find((t) => sameName(t.name, form.track));
  const concepts = track ? track.steps.map((s) => s.concept_name) : [];
  const taken = area
    ? allConcepts.filter((c) => c.area === area.id && !concepts.includes(c.name)).map((c) => c.name)
    : [];
  const fields = {
    theme: form.theme.trim(),
    goal: form.goal.trim(),
    area: form.area.trim(),
    track: form.track.trim(),
    level: form.level,
    // One word, as the backend stores it: "Gemini Notebook" becomes "gemini-notebook".
    origin: form.origin.trim().toLowerCase().replace(/\s+/g, "-"),
  };
  const request = buildRequest({ ...fields, concepts, taken });
  const answer = form.answer;

  function edit(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
    setCopied(null);
    setActionError(null);
    setMissing(null);
    // The check belongs to the exact text and destination it saw.
    if (key !== "theme" && key !== "goal" && key !== "level") {
      setReport(null);
      setCreated(null);
    }
  }

  async function copy(text, what) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(what);
    } catch {
      setCopied(`falhou:${what}`);
    }
  }

  function copyRequest() {
    const empty = [
      ["theme", "o tema"],
      ["area", "a área"],
      ["track", "a trilha"],
      ["origin", "a IA"],
    ].filter(([key]) => !fields[key]);
    setMissing(empty.length ? `Preencha ${empty.map(([, name]) => name).join(", ")}.` : null);
    if (!empty.length) copy(request, "pedido");
  }

  const body = () => ({
    area: fields.area,
    track: fields.track,
    origem: fields.origin,
    markdown: answer,
  });

  async function act(kind, request) {
    setBusy(kind);
    setActionError(null);
    try {
      await request();
    } catch (e) {
      setActionError(e.message || "O app recusou a resposta. Confira de novo para ver o motivo.");
    }
    // A check that ends during a save must not free the buttons the save holds.
    setBusy((current) => (current === kind ? null : current));
  }

  // A check answers for the exact body it was sent: a late answer for older text never counts.
  const sent = JSON.stringify(body());
  const checked = report && report.sent === sent ? report : null;

  const check = () =>
    act("check", async () => {
      const result = await api.post("/api/themes/preview/", JSON.parse(sent));
      setReport({ ...result, sent });
    });

  const save = () =>
    act("save", async () => {
      try {
        const result = await api.post("/api/themes/", JSON.parse(sent));
        setCreated(result);
        setReport(null);
        // Where Criar was, so the confirmation stays in view; it says what comes next.
        refocus.current = createdMessage;
        // Text pasted while saving is a new round: keep it.
        const saved = JSON.parse(sent).markdown;
        setForm((current) => ({ ...current, answer: current.answer === saved ? "" : current.answer }));
      } catch (e) {
        // The round may have been saved anyway: the next step is a fresh check, not this one.
        setReport(null);
        refocus.current = checkButton;
        throw e;
      } finally {
        // Also after a failure: the server may have saved a round whose answer was lost.
        await reload();
      }
    });

  // Apart from `busy`, so a retry never frees the buttons a check or a save holds.
  async function retryReload() {
    setReloading(true);
    const ok = await reload();
    setReloading(false);
    // The button leaves with the alert; the keyboard stays by the request, unless it moved on.
    if (ok && (focusLost() || document.activeElement === retryButton.current)) copyButton.current?.focus();
  }

  const blocked = checked && (checked.errors.length > 0 || checked.documents.some((d) => d.errors.length > 0));
  const toCreate = checked ? checked.documents.filter((d) => d.action === "create" || d.action === "fill") : [];
  // A concept that already exists elsewhere still joins this track, even with nothing new to write.
  const joins = checked ? checked.documents.some((d) => d.joins_track) : false;
  const correction = checked && buildCorrection(checked);
  const ready = fields.area && fields.track && fields.origin;

  return (
    <Stack gap={6} className="new-theme">
      <Stack gap={2}>
        <h1>Novo tema</h1>
        <p className="new-theme__lead">
          O Athenas monta o pedido, você cola na IA que preferir e traz a resposta de volta. Um
          conceito por rodada; os cartões chegam pendentes, para você aprovar depois de estudar.
        </p>
      </Stack>

      <Panel aria-labelledby="pedido">
        <Stack gap={5}>
          <Inline justify="between" align="baseline">
            <h2 id="pedido">Pedido para a IA</h2>
            <p className="t-meta">
              {concepts.length === 0
                ? "Primeira rodada da trilha"
                : `Rodada ${concepts.length + 1}: a trilha já tem ${concepts.length} ${
                    concepts.length === 1 ? "conceito" : "conceitos"
                  }`}
            </p>
          </Inline>
          <div className="new-theme__fields">
            <TextField
              label="Tema"
              required
              value={form.theme}
              placeholder="Docker"
              onChange={(e) => edit("theme", e.target.value)}
            />
            <TextField
              label="Objetivo"
              help="Para que você quer o tema. Muda a trilha inteira."
              value={form.goal}
              placeholder="Rodar meus projetos Django em containers"
              onChange={(e) => edit("goal", e.target.value)}
            />
            <TextField
              label="Área"
              required
              maxLength={120}
              list="novo-tema-areas"
              value={form.area}
              help={fields.area && !area ? "Área nova." : undefined}
              onChange={(e) => edit("area", e.target.value)}
            />
            <TextField
              label="Trilha"
              required
              maxLength={120}
              list="novo-tema-trilhas"
              value={form.track}
              help={fields.track && !track ? "Trilha nova." : undefined}
              onChange={(e) => edit("track", e.target.value)}
            />
            <Select
              label="Nível"
              value={form.level}
              options={LEVELS.map(([value, label]) => ({ value, label }))}
              onChange={(e) => edit("level", e.target.value)}
            />
            <TextField
              label="IA usada"
              required
              maxLength={30}
              list="novo-tema-ias"
              value={form.origin}
              placeholder="gemini"
              help="Fica marcada no conteúdo como a origem do texto."
              onChange={(e) => edit("origin", e.target.value)}
            />
          </div>
          <datalist id="novo-tema-areas">
            {areas.map((a) => (
              <option key={a.id} value={a.name} />
            ))}
          </datalist>
          <datalist id="novo-tema-trilhas">
            {tracks.map((t) => (
              <option key={t.id} value={t.name} />
            ))}
          </datalist>
          <datalist id="novo-tema-ias">
            {AIS.map((name) => (
              <option key={name} value={name} />
            ))}
          </datalist>
          {concepts.length > 0 && (
            <p className="t-meta">Já na trilha: {concepts.join(", ")}.</p>
          )}
          <Inline>
            <Button
              ref={copyButton}
              icon="copy"
              variant={answer.trim() ? "secondary" : "primary"}
              onClick={copyRequest}
            >
              Copiar pedido
            </Button>
            <CopyStatus copied={copied} what="pedido" />
          </Inline>
          <ActionError>{missing}</ActionError>
          {error && (
            // An outdated list would ask the AI for a concept the track already has.
            <Inline>
              {/* Rendered again after each retry, so a failed one is announced too. */}
              {!reloading && (
                <ActionError>
                  A lista da trilha não atualizou, então o pedido pode estar desatualizado. {error}
                </ActionError>
              )}
              <Button
                ref={retryButton}
                variant="secondary"
                loading={reloading}
                loadingLabel="Atualizando…"
                onClick={retryReload}
              >
                Atualizar a lista
              </Button>
            </Inline>
          )}
          <details className="new-theme__request">
            <summary>Ver o pedido</summary>
            <pre tabIndex={0}>{request}</pre>
          </details>
        </Stack>
      </Panel>

      <Panel aria-labelledby="resposta">
        <Stack gap={5}>
          <h2 id="resposta">Resposta da IA</h2>
          <TextArea
            label="Cole a resposta inteira"
            help="Copie pelo botão de copiar do bloco de código da IA: selecionar o texto da tela perde os títulos."
            rows={12}
            value={answer}
            spellCheck={false}
            onChange={(e) => edit("answer", e.target.value)}
          />
          <Inline>
            <Button
              ref={checkButton}
              variant={checked && !blocked ? "secondary" : "primary"}
              icon="file-text"
              loading={busy === "check"}
              loadingLabel="Conferindo…"
              disabled={!answer.trim() || !ready || busy === "save"}
              onClick={check}
            >
              Conferir
            </Button>
            {checked && !blocked && (toCreate.length > 0 || joins) && (
              <Button
                icon="check"
                loading={busy === "save"}
                loadingLabel="Criando…"
                disabled={busy === "check"}
                onClick={save}
              >
                {toCreate.length === 0
                  ? "Pôr na trilha"
                  : toCreate.length === 1
                    ? "Criar 1 subtema"
                    : `Criar ${toCreate.length} subtemas`}
              </Button>
            )}
          </Inline>
          {!ready && answer.trim() && (
            <p className="t-meta">Preencha área, trilha e IA usada para conferir.</p>
          )}
          <ActionError>
            {actionError && `Não foi possível concluir. A resposta continua aqui. ${actionError}`}
          </ActionError>
          {created && (
            <div ref={createdMessage} tabIndex={-1}>
              <Created result={created} stale={error} />
            </div>
          )}
          {checked && (
            <Report report={checked} blocked={blocked} toCreate={toCreate.length} joins={joins}>
              {correction && (
                <>
                  <Inline>
                    <Button
                      variant="secondary"
                      icon="copy"
                      onClick={() => copy(correction, "correção")}
                    >
                      Copiar pedido de correção
                    </Button>
                    <CopyStatus copied={copied} what="correção" />
                  </Inline>
                  <details className="new-theme__request">
                    <summary>Ver o pedido de correção</summary>
                    <pre tabIndex={0}>{correction}</pre>
                  </details>
                </>
              )}
            </Report>
          )}
        </Stack>
      </Panel>
    </Stack>
  );
}

function CopyStatus({ copied, what }) {
  if (copied === what) {
    return (
      <p className="t-meta" role="status">
        Copiado. Cole na IA.
      </p>
    );
  }
  if (copied === `falhou:${what}`) {
    return (
      <p className="ui-field__error" role="alert">
        O navegador não deixou copiar. Abra o texto e copie à mão.
      </p>
    );
  }
  return null;
}

function Report({ report, blocked, toCreate, joins, children }) {
  const { documents, errors, warnings } = report;
  return (
    <Stack as="section" gap={4} aria-labelledby="conferencia">
      <h3 id="conferencia">Conferência</h3>
      {report.complete ? (
        <StateMessage kind="success" title="A trilha está completa.">
          A IA disse que os conceitos da trilha já cobrem o tema. Nada foi criado.
        </StateMessage>
      ) : (
        errors.length > 0 && (
          <StateMessage kind="error" title="Nada foi criado.">
            {errors.join(" ")}
          </StateMessage>
        )
      )}
      {documents.length > 0 && (
        <p className="t-meta" role="status">
          {blocked
            ? "Corrija os erros marcados antes de criar; nada é criado pela metade."
            : toCreate === 0
              ? joins
                ? "Os subtemas já estão no app. Falta só pôr o conceito nesta trilha."
                : "Nada novo nesta resposta: todos os subtemas já estão no app."
              : `${report.area_new ? "Área nova. " : ""}${report.track_new ? "Trilha nova. " : ""}Os avisos não impedem criar: o conteúdo incompleto entra como rascunho.`}
        </p>
      )}
      {warnings.length > 0 && (
        <Callout variant="info" title="Não entra no app">
          <ul>
            {warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </Callout>
      )}
      {documents.length > 0 && (
        <List label="Documentos da resposta">
          {documents.map((d, i) => (
            // A row of the house list with the document's problems under its title.
            <li key={i} className="ui-list__row">
              <div className="ui-list__main">
                <span className="ui-list__title">
                  {d.conceito || "Sem conceito"} / {d.subtema || "sem subtema"}
                </span>
                <span className="t-meta">{rowMeta(d)}</span>
                <Problems items={d.errors} error />
                <Problems items={d.warnings} />
              </div>
              <div className="ui-list__badges">
                {d.generated_by && <GeneratedByBadge by={d.generated_by} />}
                {d.errors.length > 0 ? (
                  <Badge tone="error" icon="alert-circle">
                    Impede criar
                  </Badge>
                ) : d.state === "ready" ? (
                  <Badge tone="success" icon="check-circle">
                    Pronto
                  </Badge>
                ) : (
                  <Badge icon="file-text">Rascunho</Badge>
                )}
              </div>
            </li>
          ))}
        </List>
      )}
      {children}
    </Stack>
  );
}

function rowMeta(d) {
  const parts = [
    `${ACTIONS[d.action]}${d.concept_new ? ", conceito novo" : ""}`,
    `${d.questions} ${d.questions === 1 ? "pergunta" : "perguntas"}`,
    `${d.cards} ${d.cards === 1 ? "cartão" : "cartões"}`,
  ];
  if (d.unsourced) parts.push(`${d.unsourced} sem fonte`);
  return parts.join(" · ");
}

function Problems({ items, error = false }) {
  if (!items.length) return null;
  return (
    <ul className={`new-theme__problems${error ? " new-theme__problems--error" : ""}`}>
      {items.map((p) => (
        <li key={p}>
          {error && <strong>Impede criar: </strong>}
          {p}
        </li>
      ))}
    </ul>
  );
}

function Created({ result, stale }) {
  const made = result.documents.filter((d) => d.action === "create" || d.action === "fill");
  const names = (docs) => [...new Set(docs.map((d) => d.conceito))].join(", ");
  // Without the reload the next request would list an outdated track.
  const next = stale
    ? "A lista da trilha não atualizou: atualize-a no pedido, acima, antes de copiá-lo de novo."
    : "Para o próximo conceito, copie o pedido de novo: ele já lista o que a trilha tem.";
  if (!made.length) {
    return (
      <StateMessage
        kind="success"
        title={`${names(result.documents)} entrou na trilha.`}
        action={<a href={`#/roadmap/${result.track}`}>Abrir o Roadmap</a>}
      >
        {stale && next}
      </StateMessage>
    );
  }
  return (
    <StateMessage
      kind="success"
      title={`${made.length === 1 ? "1 subtema criado" : `${made.length} subtemas criados`} em ${names(made)}.`}
      action={
        <Inline>
          <a href={`#/roadmap/${result.track}`}>Abrir o Roadmap</a>
          <a href="#/biblioteca">Abrir a Biblioteca</a>
        </Inline>
      }
    >
      {result.pending === 1
        ? "1 cartão espera a sua aprovação"
        : `${result.pending} cartões esperam a sua aprovação`}
      , na Biblioteca, depois que você estudar cada subtema. {next}
    </StateMessage>
  );
}
