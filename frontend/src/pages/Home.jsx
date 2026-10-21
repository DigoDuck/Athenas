import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../api.js";
import { Button, Icon, Panel, StateMessage } from "../ui/index.js";
import "./home.css";

// Home screen (spec 4.5.2): continue where I stopped, then today's reviews, then each track's
// next step. Every load records `app_opened` through POST /api/home/ (DECISIONS.md D-026).
// A return session (spec 4.7) shows only the first two, and no text mentions the absence.
// The opening lines sit on the panorama's light side; the rest is on one opaque board.
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
      <div className="scenic">
        <h1>Início</h1>
        <Panel raised className="scenic__board">
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

  const stop = home.last_stop;
  return (
    <div className="scenic">
      <LastStop stop={stop} />
      <Panel raised className="scenic__board">
        {(home.next_steps.length > 0 || stop) && (
          <div className="home__columns">
            {home.next_steps.length > 0 && <NextSteps steps={home.next_steps} />}
            {stop && (
              <section className="home__column" aria-labelledby="home-practice">
                <h2 id="home-practice">Coloque em palavras</h2>
                <div className="home__item">
                  <Icon name="pencil" size={32} />
                  <p className="home__lead">Pratique o conteúdo que está estudando.</p>
                </div>
                <div className="home__indent">
                  <Button variant="secondary" icon="pencil" href={`#/pratica/${stop.subtopic}`}>
                    Abrir prática
                  </Button>
                </div>
              </section>
            )}
          </div>
        )}
        <section className="home__reviews" aria-labelledby="home-reviews">
          <Icon name="reviews" size={28} />
          <h2 id="home-reviews">Revisões de hoje</h2>
          {home.reviews_today > 0 ? (
            <>
              <p>
                {home.reviews_today === 1 ? "1 cartão para hoje." : `${home.reviews_today} cartões para hoje.`}
              </p>
              <Button variant="tertiary" href="#/revisoes" iconEnd="arrow-right">
                Revisar
              </Button>
            </>
          ) : (
            <p>Nenhum cartão para hoje.</p>
          )}
        </section>
      </Panel>
    </div>
  );
}

function LastStop({ stop }) {
  return (
    <section className="scenic__hero" aria-labelledby="home-title">
      <h1>Início</h1>
      {stop ? (
        <>
          <p className="scenic__eyebrow">Continue de onde parou</p>
          <h2 id="home-title" className="scenic__title">
            {stop.subtopic_name}
          </h2>
          <p className="scenic__subtitle">{stop.concept_name}</p>
          {stop.block_heading && (
            <p className="scenic__note">
              Retome no bloco <strong>{stop.block_heading}</strong>.
            </p>
          )}
          <div className="scenic__action">
            <Button href={`#/estudo/${stop.subtopic}`} iconEnd="arrow-right">
              Continuar leitura
            </Button>
          </div>
        </>
      ) : (
        <>
          <p className="scenic__eyebrow">Uma etapa de cada vez</p>
          <h2 id="home-title" className="scenic__title">
            Comece pela Biblioteca
          </h2>
          <p className="scenic__note">Escolha um subtema e abra o primeiro bloco.</p>
          <div className="scenic__action">
            <Button href="#/biblioteca" iconEnd="arrow-right">
              Abrir a Biblioteca
            </Button>
          </div>
        </>
      )}
    </section>
  );
}

function NextSteps({ steps }) {
  return (
    <section className="home__column" aria-labelledby="home-path">
      <h2 id="home-path">Seu percurso</h2>
      <ul className="home__steps">
        {steps.map((step) => (
          <li key={step.track_name} className="home__item">
            <Icon name="graduation" size={32} />
            <div>
              <p className="home__lead">{step.track_name}</p>
              <p className="home__meta">
                Próximo passo: {step.concept_name}
                {step.subtopic_name && ` · ${step.subtopic_name}`}
              </p>
            </div>
          </li>
        ))}
      </ul>
      <div className="home__indent">
        <Button variant="tertiary" href="#/roadmap" iconEnd="arrow-right" className="home__link">
          Ver roadmap
        </Button>
      </div>
    </section>
  );
}
