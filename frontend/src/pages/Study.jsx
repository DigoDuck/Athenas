import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../api.js";
import CompletionSuggestion from "./CompletionSuggestion.jsx";
import {
  Badge,
  Breadcrumb,
  Button,
  Callout,
  calloutBody,
  GeneratedByBadge,
  Icon,
  Inline,
  Markdown,
  markdownLinks,
  safeUrl,
  Panel,
  ProgressBar,
  Stack,
  StateMessage,
} from "../ui/index.js";
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
  const sheet = useRef(null);
  const end = useRef(null);
  // StrictMode runs effects twice in dev; the first block must start one event, not two.
  const started = useRef(false);
  // Leaving the screen while it loads must not start a reading nobody sees.
  const mounted = useRef(false);

  const fetchReading = useCallback(
    () => api.get(`/api/subtopics/${subtopicId}/reading/`),
    [subtopicId],
  );

  // The event starts first and the blocks are fetched after it, so the text on screen is never
  // older than the event: a re-import the screen did not show leaves the block unread (D-023).
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
        const data = await fetchReading();
        setEvent(created);
        setReading(data);
        setOrder(next);
      } catch (e) {
        setError(`Não foi possível abrir o bloco. ${e.message}`);
        // A re-import may have removed that block; the fresh blocks show it.
        fetchReading().then(setReading, () => {});
      }
      setBusy(null);
    },
    [subtopicId, fetchReading],
  );

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      const data = await fetchReading();
      if (!mounted.current) return;
      setReading(data);
      if (data.blocks.length > 0) await open(data.resume_block_order);
    } catch (e) {
      if (mounted.current) setLoadError(e);
    }
  }, [fetchReading, open]);

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

  // A new block takes the reader to its sheet, so keyboard and screen reader users follow along.
  useEffect(() => {
    if (order === null) return;
    sheet.current?.focus();
  }, [order]);

  // The last "Li este bloco" button disappears; focus moves to what replaced it.
  useEffect(() => {
    if (finished) end.current?.focus();
  }, [finished]);

  async function markRead() {
    setBusy("read");
    setError(null);
    try {
      // Already completed when only opening the next block failed: retrying just opens it.
      if (!event.completed_at) {
        setEvent(await api.post(`/api/events/${event.id}/complete/`));
      }
      // The server decides whether the block was marked read (D-023) and how many blocks there
      // are now; next or finished follows its answer.
      const data = await fetchReading();
      setReading(data);
      if (order < data.blocks.length - 1) {
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
    const missing = loadError?.status === 404;
    return (
      <Stack gap={6}>
        <Breadcrumb items={[{ label: "Biblioteca", href: "#/biblioteca" }, { label: "Estudo" }]} />
        <h1>Estudo</h1>
        {missing ? (
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
  const unread = blocks.filter((b) => !b.read_at);
  const last = order === blocks.length - 1;

  return (
    <div className="study">
      {blocks.length > 0 && (
        <nav className="study__outline" aria-label="Blocos do subtema">
          <p className="study__label">Neste subtema</p>
          <ol>
            {blocks.map((b, index) => (
              <li key={b.order}>
                <button
                  type="button"
                  className="study__outline-item"
                  aria-current={index === order ? "step" : undefined}
                  data-read={b.read_at ? "" : undefined}
                  disabled={busy !== null}
                  onClick={() => index !== order && open(index)}
                >
                  <Icon name={b.read_at ? "check-circle" : "circle"} />
                  <span>{b.heading || "Introdução"}</span>
                  {b.read_at && <span className="visually-hidden"> (lido)</span>}
                </button>
              </li>
            ))}
          </ol>
        </nav>
      )}
      <Stack gap={6} className="study__head">
        <Breadcrumb
          items={[
            { label: "Biblioteca", href: "#/biblioteca" },
            { label: reading.concept, href: "#/biblioteca" },
            { label: reading.subtopic },
          ]}
        />
        <Stack gap={3}>
          <h1>{reading.subtopic}</h1>
          {reading.generated_by && (
            <Inline gap={2}>
              <GeneratedByBadge by={reading.generated_by} />
              <p className="t-meta">Bem escrito não quer dizer correto: confira nas Fontes.</p>
            </Inline>
          )}
          {blocks.length > 0 && (
            <ProgressBar
              value={blocks.length - unread.length}
              max={blocks.length}
              unit="blocos lidos"
              label="Blocos lidos"
            />
          )}
        </Stack>
      </Stack>
      <Stack gap={6} className="study__column">
        {blocks.length === 0 ? (
          <StateMessage
            title="Este subtema ainda não tem conteúdo."
            action={<Button href="#/biblioteca">Voltar à Biblioteca</Button>}
          >
            Cole o Markdown dele em Conteúdo, na Biblioteca, e volte aqui para estudar.
          </StateMessage>
        ) : block ? (
          <Panel
            raised
            ref={sheet}
            tabIndex={-1}
            aria-labelledby="bloco-titulo"
            className="study__block"
          >
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
            <h2 id="bloco-titulo" className={block.heading ? undefined : "visually-hidden"}>
              {block.heading || "Introdução"}
            </h2>
            <Segments segments={block.segments} />
            <ActionError>{error}</ActionError>
            {finished && (
              <div ref={end} tabIndex={-1}>
                {unread.length > 0 ? (
                  <StateMessage
                    title="Você chegou ao último bloco."
                    action={
                      <Button onClick={() => open(unread[0].order)}>
                        Ir para o primeiro bloco sem leitura
                      </Button>
                    }
                  >
                    {unread.length === 1
                      ? "Ainda há 1 bloco sem leitura."
                      : `Ainda há ${unread.length} blocos sem leitura.`}
                  </StateMessage>
                ) : (
                  <StateMessage
                    kind="success"
                    title="Você leu todos os blocos deste subtema."
                    action={
                      <Button href={`#/pratica/${subtopicId}`} iconEnd="arrow-right">
                        Praticar
                      </Button>
                    }
                  >
                    Uma etapa de cada vez. Agora, veja o que ficou respondendo sem consultar.
                  </StateMessage>
                )}
              </div>
            )}
            <Inline justify="between" className="study__actions">
              <Button
                variant="secondary"
                icon="arrow-left"
                disabled={order === 0 || busy !== null}
                onClick={() => open(order - 1)}
              >
                Anterior
              </Button>
              {!finished && (
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
              )}
            </Inline>
          </Panel>
        ) : order !== null ? (
          // A re-import left fewer blocks than the one being read.
          <Stack gap={3}>
            <StateMessage
              title="O conteúdo deste subtema mudou."
              action={
                <Button
                  loading={busy === "open"}
                  loadingLabel="Abrindo…"
                  onClick={() => open(blocks.length - 1)}
                >
                  Continuar a leitura
                </Button>
              }
            >
              O bloco que estava aberto não existe mais.
            </StateMessage>
            <ActionError>{error}</ActionError>
          </Stack>
        ) : (
          <Panel aria-label="Bloco">
            {error ? <ActionError>{error}</ActionError> : <p className="t-meta">Abrindo o bloco…</p>}
            {error && (
              <Button onClick={() => open(reading.resume_block_order)}>Tentar novamente</Button>
            )}
          </Panel>
        )}
        {finished && <CompletionSuggestion subtopicId={subtopicId} />}
      </Stack>
      {blocks.length > 0 && <Aside blocks={blocks} subtopicId={subtopicId} />}
    </div>
  );
}

// What sits beside the text: the subtopic's sources and the way to practice after reading.
function Aside({ blocks, subtopicId }) {
  const sources = markdownLinks(
    blocks
      .flatMap((b) => b.segments.filter((s) => b.kind === "Fontes" || s.kind === "ia"))
      .map((s) => s.text)
      .join("\n"),
  );
  return (
    <aside className="study__aside" aria-label="Apoio à leitura">
      {sources.length > 0 && (
        <Panel aria-labelledby="study-sources">
          <h2 id="study-sources" className="study__label">
            Fontes
          </h2>
          <ul className="study__sources">
            {sources.map(({ url, label }) => (
              <li key={url}>
                <a href={url} target="_blank" rel="noreferrer" title={url}>
                  {label ?? siteName(url)}
                </a>
              </li>
            ))}
          </ul>
        </Panel>
      )}
      <Panel aria-labelledby="study-practice">
        <Stack gap={3}>
          <h2 id="study-practice" className="study__label">
            Depois da leitura
          </h2>
          <p className="t-meta">Responda às perguntas deste subtema sem consultar o texto.</p>
          <div>
            <Button variant="secondary" href={`#/pratica/${subtopicId}`} iconEnd="arrow-right">
              Praticar
            </Button>
          </div>
        </Stack>
      </Panel>
    </aside>
  );
}

function siteName(url) {
  try {
    return new URL(url, window.location.href).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

// A stored image with its credit, which lives with the image so it is never left out: a diagram
// an AI drew carries the D-032 badge, a real picture its author, license and page (D-033).
function Figure({ image }) {
  const credit = image.generated_by ? (
    <GeneratedByBadge by={image.generated_by} />
  ) : (
    <>
      {image.author}, {image.license}
      {safeUrl(image.source_url) && (
        <>
          {" · "}
          <a href={image.source_url} target="_blank" rel="noreferrer">
            {siteName(image.source_url)}
          </a>
        </>
      )}
    </>
  );
  return (
    <div className="ui-markdown">
      <figure>
        {image.url ? (
          <img src={image.url} alt={image.caption} loading="lazy" />
        ) : (
          <p className="t-meta">Imagem não encontrada.</p>
        )}
        <figcaption>
          {image.caption}
          {image.url && <span className="study__credit">{credit}</span>}
        </figcaption>
      </figure>
    </div>
  );
}

// The body as the API cut it: Markdown text, fenced code, `[!ia]` callouts, which carry
// "complemento sem fonte" when they have no source (spec 4.2.8), and images.
function Segments({ segments }) {
  if (segments.length === 0) return <p className="t-meta">Este bloco não tem texto.</p>;
  return (
    <div className="t-reading">
      {segments.map((segment, index) =>
        segment.kind === "code" ? (
          <pre key={index}>
            <code>{segment.text}</code>
          </pre>
        ) : segment.kind === "ia" ? (
          <Callout key={index} variant="ai" source={segment.source}>
            <Markdown text={calloutBody(segment.text)} />
          </Callout>
        ) : segment.kind === "image" ? (
          <Figure key={index} image={segment.image} />
        ) : (
          <Markdown key={index} text={segment.text} />
        ),
      )}
    </div>
  );
}
