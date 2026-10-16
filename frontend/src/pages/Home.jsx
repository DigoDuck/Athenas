import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../api.js";
import { Button, Inline, Panel, Stack, StateMessage } from "../ui/index.js";
import "./home.css";

// Home screen (spec 4.5.2): continue where I stopped, then today's reviews, then each track's
// next step. Every load records `app_opened` through POST /api/home/ (DECISIONS.md D-026).
// A return session (spec 4.7) shows only the first two, and no text mentions the absence.
// The scene is the statue panorama, so every piece of text sits in an opaque Panel.
export default function Home() {
  const [home, setHome] = useState(null);
  const [error, setError] = useState(null);
  // StrictMode runs effects twice in dev; one load is one `app_opened`, not two.
  const loaded = useRef(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      setHome(await api.post("/api/home/"));
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;
    load();
  }, [load]);

  if (error || !home) {
    return (
      <div className="home">
        <Panel raised>
          {error ? (
            <StateMessage
              kind="error"
              title="Não foi possível carregar o início."
              action={<Button onClick={load}>Tentar novamente</Button>}
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

  return (
    <div className="home">
      <LastStop stop={home.last_stop} />
      <Panel as="section" aria-labelledby="home-reviews">
        <Inline justify="between">
          <h2 id="home-reviews" className="home__reviews">
            Revisões de hoje: {home.reviews_today}
          </h2>
          {home.reviews_today > 0 && (
            <Button variant="secondary" href="#/revisoes" iconEnd="arrow-right">
              Revisar
            </Button>
          )}
        </Inline>
      </Panel>
      {home.next_steps.length > 0 && <NextSteps steps={home.next_steps} />}
    </div>
  );
}

function LastStop({ stop }) {
  if (!stop) {
    return (
      <Panel raised aria-labelledby="home-title">
        <Stack gap={3}>
          <h1 id="home-title" className="t-display">
            Uma etapa de cada vez
          </h1>
          <p>Escolha um subtema na Biblioteca e abra o primeiro bloco.</p>
        </Stack>
        <div>
          <Button href="#/biblioteca" iconEnd="arrow-right">
            Abrir a Biblioteca
          </Button>
        </div>
      </Panel>
    );
  }
  return (
    <Panel raised aria-labelledby="home-title">
      <Stack gap={3}>
        <h1 id="home-title" className="t-display">
          Continue de onde parou
        </h1>
        <Stack gap={1}>
          <p className="home__subtopic">{stop.subtopic_name}</p>
          <p className="t-meta">
            {stop.concept_name}
            {stop.block_heading && ` · ${stop.block_heading}`}
          </p>
        </Stack>
      </Stack>
      <div>
        <Button href={`#/estudo/${stop.subtopic}`} iconEnd="arrow-right">
          Continuar
        </Button>
      </div>
    </Panel>
  );
}

function NextSteps({ steps }) {
  return (
    <Panel as="section" aria-labelledby="home-next">
      <h2 id="home-next" className="t-section-title">
        Próximo passo
      </h2>
      <ul className="home__steps">
        {steps.map((step) => (
          <li key={step.track_name} className="home__step">
            <div>
              <p className="home__concept">{step.concept_name}</p>
              <p className="t-meta">
                {step.track_name}
                {step.subtopic_name && ` · ${step.subtopic_name}`}
              </p>
            </div>
            {step.subtopic ? (
              <Button
                variant="tertiary"
                href={`#/estudo/${step.subtopic}`}
                aria-label={`Estudar ${step.subtopic_name}`}
              >
                Estudar
              </Button>
            ) : (
              <Button
                variant="tertiary"
                href="#/biblioteca"
                aria-label={`Preparar ${step.concept_name} na Biblioteca`}
              >
                Preparar na Biblioteca
              </Button>
            )}
          </li>
        ))}
      </ul>
    </Panel>
  );
}
