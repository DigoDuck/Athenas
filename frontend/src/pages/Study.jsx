import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../api.js";
import { Badge, Breadcrumb, Button, Inline, Panel, ProgressBar, Stack, StateMessage } from "../ui/index.js";
import { ActionError } from "./forms.jsx";
import "./study.css";

// Reading, one block at a time in document order (spec 4.8.1, DECISIONS.md D-020).
// Opening a block starts a reading event; "Li este bloco" completes it and marks the block read.
// Reopening the subtopic resumes at the last block opened, so closing the browser loses nothing.
export default function Study({ subtopicId }) {
  const [reading, setReading] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [order, setOrder] = useState(null);
  const [event, setEvent] = useState(null);
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState(null);
  const [finished, setFinished] = useState(false);
  const heading = useRef(null);
  // StrictMode runs effects twice in dev; the first block must start one event, not two.
  const started = useRef(false);

  const open = useCallback(
    async (next) => {
      setBusy("open");
      setError(null);
      setFinished(false);
      try {
        const created = await api.post("/api/events/", {
          kind: "reading",
          subtopic: subtopicId,
          block_order: next,
        });
        setEvent(created);
        setOrder(next);
      } catch (e) {
        setError(`Não foi possível abrir o bloco. ${e.message}`);
      }
      setBusy(null);
    },
    [subtopicId],
  );

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      const data = await api.get(`/api/subtopics/${subtopicId}/reading/`);
      setReading(data);
      await open(data.resume_block_order);
    } catch (e) {
      setLoadError(e);
    }
  }, [subtopicId, open]);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    load();
  }, [load]);

  // A new block takes the reader to its heading, so keyboard and screen reader users follow along.
  useEffect(() => {
    if (order === null) return;
    heading.current?.focus();
  }, [order]);

  async function markRead() {
    setBusy("read");
    setError(null);
    try {
      const done = await api.post(`/api/events/${event.id}/complete/`);
      setReading((r) => ({
        ...r,
        blocks: r.blocks.map((b) =>
          b.order === order && !b.read_at ? { ...b, read_at: done.completed_at } : b,
        ),
      }));
      if (order < reading.blocks.length - 1) {
        setBusy(null);
        await open(order + 1);
        return;
      }
      setFinished(true);
    } catch (e) {
      setError(`Não foi possível marcar como lido. ${e.message}`);
    }
    setBusy(null);
  }

  if (loadError || !reading) {
    const empty = loadError?.status === 404;
    return (
      <Stack gap={6}>
        <Breadcrumb items={[{ label: "Biblioteca", href: "#/biblioteca" }, { label: "Estudo" }]} />
        <h1>Estudo</h1>
        {empty ? (
          <StateMessage
            title="Este subtema ainda não tem conteúdo."
            action={<Button href="#/biblioteca">Voltar à Biblioteca</Button>}
          >
            Cole o Markdown dele em Conteúdo, na Biblioteca, e volte aqui para estudar.
          </StateMessage>
        ) : loadError ? (
          <StateMessage
            kind="error"
            title="Não foi possível carregar a leitura."
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

  const { blocks } = reading;
  const block = order === null ? null : blocks[order];
  const readCount = blocks.filter((b) => b.read_at).length;
  const last = order === blocks.length - 1;

  return (
    <Stack gap={6}>
      <Breadcrumb
        items={[
          { label: "Biblioteca", href: "#/biblioteca" },
          { label: reading.concept, href: "#/biblioteca" },
          { label: reading.subtopic },
        ]}
      />
      <Stack gap={6} className="study__column">
        <Stack gap={3}>
          <h1>{reading.subtopic}</h1>
          <ProgressBar value={readCount} max={blocks.length} unit="blocos lidos" label="Blocos lidos" />
        </Stack>
        {block ? (
          <Panel raised aria-labelledby="bloco-titulo" className="study__block">
            <Inline justify="between">
              <p className="t-meta">
                Bloco {order + 1} de {blocks.length}
              </p>
              {block.read_at && (
                <Badge tone="success" icon="check-circle">
                  Lido
                </Badge>
              )}
            </Inline>
            {/* Text before the first heading is an extra block with no heading (D-014). */}
            <h2
              id="bloco-titulo"
              ref={heading}
              tabIndex={-1}
              className={block.heading ? undefined : "visually-hidden"}
            >
              {block.heading || "Introdução"}
            </h2>
            <div className="t-reading study__body">{block.body}</div>
            <ActionError>{error}</ActionError>
            {finished ? (
              <StateMessage
                kind="success"
                title="Você chegou ao fim deste subtema."
                action={<Button href="#/biblioteca">Voltar à Biblioteca</Button>}
              >
                Uma etapa de cada vez.
              </StateMessage>
            ) : (
              <Inline justify="between" className="study__actions">
                <Button
                  variant="secondary"
                  icon="arrow-left"
                  disabled={order === 0 || busy !== null}
                  onClick={() => open(order - 1)}
                >
                  Anterior
                </Button>
                <Button
                  icon={last ? "check" : undefined}
                  iconEnd={last ? undefined : "arrow-right"}
                  loading={busy === "read"}
                  loadingLabel="Marcando…"
                  disabled={busy === "open" || !event}
                  onClick={markRead}
                >
                  {last ? "Li este bloco" : "Li este bloco, próximo"}
                </Button>
              </Inline>
            )}
          </Panel>
        ) : (
          <Panel aria-label="Bloco">
            {error ? <ActionError>{error}</ActionError> : <p className="t-meta">Abrindo o bloco…</p>}
            {error && <Button onClick={() => open(reading.resume_block_order)}>Tentar novamente</Button>}
          </Panel>
        )}
      </Stack>
    </Stack>
  );
}
