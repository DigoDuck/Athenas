import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../api.js";
import {
  Breadcrumb,
  Button,
  GeneratedByBadge,
  Inline,
  Panel,
  Stack,
  StateMessage,
} from "../ui/index.js";
import { ActionError } from "./forms.jsx";
import { Segments } from "./Study.jsx";
import "./study.css";
import "./notebook.css";

const listFormat = new Intl.ListFormat("pt-BR", { type: "conjunction" });

// Notebook mode (spec 4.8.2, DECISIONS.md D-036): Objetivo, Ideia central, Exemplo and Resumo para
// o caderno on one sheet, then one prompt to answer on paper. Opening the screen starts a
// notebook event; "Copiei para o caderno" completes it. Nothing here marks blocks read.
export default function Notebook({ subtopicId }) {
  const [page, setPage] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [event, setEvent] = useState(null);
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState(null);
  const done = useRef(null);
  // StrictMode runs effects twice in dev; one visit must start one event, not two.
  const started = useRef(false);
  // Leaving the screen while it loads must not start an activity nobody sees.
  const mounted = useRef(false);

  const start = useCallback(async () => {
    setBusy("start");
    setError(null);
    try {
      const created = await api.post("/api/events/", { kind: "notebook", subtopic: subtopicId });
      if (mounted.current) setEvent(created);
    } catch (e) {
      if (mounted.current) setError(`Não foi possível começar o caderno. ${e.message}`);
    }
    if (mounted.current) setBusy(null);
  }, [subtopicId]);

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      const data = await api.get(`/api/subtopics/${subtopicId}/notebook/`);
      if (!mounted.current) return;
      setPage(data);
      if (data.blocks.length > 0) await start();
    } catch (e) {
      if (mounted.current) setLoadError(e);
    }
  }, [subtopicId, start]);

  useEffect(() => {
    mounted.current = true;
    if (!started.current) {
      started.current = true;
      load();
    }
    return () => {
      mounted.current = false;
    };
  }, [load]);

  // The button disappears once the copy is recorded; focus moves to what replaced it.
  useEffect(() => {
    if (event?.completed_at) done.current?.focus();
  }, [event?.completed_at]);

  async function complete() {
    setBusy("complete");
    setError(null);
    try {
      setEvent(await api.post(`/api/events/${event.id}/complete/`));
    } catch (e) {
      // 409 means an earlier try was saved and only its answer was lost.
      if (e.status === 409) setEvent({ ...event, completed_at: new Date().toISOString() });
      else setError(`Não foi possível registrar o caderno. ${e.message}`);
    }
    setBusy(null);
  }

  const crumbs = [
    { label: "Biblioteca", href: "#/biblioteca" },
    ...(page ? [{ label: page.concept, href: "#/biblioteca" }] : []),
    ...(page ? [{ label: page.subtopic, href: `#/estudo/${subtopicId}` }] : []),
    { label: "Modo caderno" },
  ];

  if (loadError || !page) {
    return (
      <Stack gap={6}>
        <Breadcrumb items={crumbs} />
        <h1>Modo caderno</h1>
        {loadError?.status === 404 ? (
          <StateMessage
            kind="error"
            title="Este subtema não existe mais."
            action={<Button href="#/biblioteca">Voltar à Biblioteca</Button>}
          >
            Escolha outro subtema na Biblioteca.
          </StateMessage>
        ) : loadError ? (
          <StateMessage
            kind="error"
            title="Não foi possível carregar o caderno."
            action={<Button onClick={load}>Tentar novamente</Button>}
          >
            {loadError.message}
          </StateMessage>
        ) : (
          <p className="t-meta">Carregando…</p>
        )}
      </Stack>
    );
  }

  const { blocks, missing, question } = page;
  const prompt = question
    ? `${question.label}: ${question.prompt}`
    : `Explique ${page.subtopic} com suas palavras, como se estivesse ensinando alguém.`;

  return (
    <Stack gap={6} className="notebook">
      <Stack gap={4}>
        <div data-print="hide">
          <Breadcrumb items={crumbs} />
        </div>
        <h1>{page.subtopic}</h1>
        {page.generated_by && (
          <div className="study__provenance">
            <GeneratedByBadge by={page.generated_by} />
            <p className="t-meta">Confira o conteúdo nas fontes.</p>
          </div>
        )}
      </Stack>
      {blocks.length === 0 ? (
        <StateMessage
          title="Ainda não há o que copiar deste subtema."
          action={<Button href="#/biblioteca">Voltar à Biblioteca</Button>}
        >
          O caderno usa Objetivo, Ideia central, Exemplo e Resumo para o caderno. Cole o Markdown
          do subtema em Conteúdo, na Biblioteca.
        </StateMessage>
      ) : (
        <Panel raised className="notebook__sheet">
          {blocks.map((block) => (
            <section key={block.order} aria-labelledby={`caderno-${block.order}`} className="notebook__section">
              <h2 id={`caderno-${block.order}`}>{block.heading}</h2>
              <Segments segments={block.segments} />
            </section>
          ))}
          <section aria-labelledby="caderno-pratica" className="notebook__section notebook__prompt">
            <h2 id="caderno-pratica">Responda sem consultar</h2>
            <p className="t-reading">{prompt}</p>
            <p className="t-meta" data-print="hide">
              Escreva a resposta no caderno. Para comparar com a resposta de referência, responda
              também na Prática.
            </p>
          </section>
          {missing.length > 0 && (
            <p className="t-meta">Este subtema não tem {listFormat.format(missing)}.</p>
          )}
          <div className="notebook__actions" data-print="hide">
            {event?.completed_at ? (
              <div ref={done} tabIndex={-1}>
                <StateMessage
                  kind="success"
                  title="Caderno registrado."
                  action={
                    <Inline gap={3}>
                      <Button variant="secondary" href={`#/estudo/${subtopicId}`}>
                        Voltar à leitura
                      </Button>
                      <Button href={`#/pratica/${subtopicId}`} iconEnd="arrow-right">
                        Praticar
                      </Button>
                    </Inline>
                  }
                >
                  Uma etapa de cada vez.
                </StateMessage>
              </div>
            ) : (
              <>
                <ActionError>{error}</ActionError>
                {event ? (
                  <Button
                    icon="check"
                    loading={busy === "complete"}
                    loadingLabel="Registrando…"
                    onClick={complete}
                  >
                    Copiei para o caderno
                  </Button>
                ) : (
                  <Button loading={busy === "start"} loadingLabel="Começando…" onClick={start}>
                    Tentar novamente
                  </Button>
                )}
              </>
            )}
          </div>
        </Panel>
      )}
    </Stack>
  );
}
