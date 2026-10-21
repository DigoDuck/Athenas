import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { api } from "../api.js";
import { Button, Icon } from "../ui/index.js";
import "./pomodoro.css";

// Pomodoro (spec 4.9, DECISIONS.md D-037): optional, in the navigation, away from the content.
// A focus is followed by its break on its own, then the timer stops. Each end gives one notice
// in a corner that never takes focus or blocks the page. The timer lives in localStorage as an
// end time, so it survives a reload and counts right in a background tab.

const KEY = "athenas.pomodoro";
const MINUTE = 60_000;

function readTimer() {
  try {
    const timer = JSON.parse(localStorage.getItem(KEY));
    return Number.isFinite(timer?.endsAt) ? timer : null;
  } catch {
    return null;
  }
}

function writeTimer(timer) {
  try {
    if (timer) localStorage.setItem(KEY, JSON.stringify(timer));
    else localStorage.removeItem(KEY);
  } catch {
    // Without storage the timer still runs; it only stops surviving a reload.
  }
}

// The timer at `now`: a finished focus turns into its break, counted from the focus's end;
// a finished break, or a focus whose break also passed, ends the timer.
function settle(timer, now) {
  if (!timer || now < timer.endsAt) return timer;
  if (timer.phase === "focus") {
    const endsAt = timer.endsAt + timer.breakMinutes * MINUTE;
    if (now < endsAt) return { phase: "break", endsAt };
  }
  return null;
}

function clock(ms) {
  const seconds = Math.max(Math.ceil(ms / 1000), 0);
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

export default function Pomodoro() {
  // A phase that ended while the app was closed settles silently: the notice is for the moment.
  const [timer, setTimer] = useState(() => settle(readTimer(), Date.now()));
  const [now, setNow] = useState(Date.now);
  const [notice, setNotice] = useState(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);

  // Starting or stopping swaps the button; the new one takes the focus, so it is not lost.
  const control = useRef(null);
  const moveFocus = useRef(false);

  useEffect(() => {
    writeTimer(timer);
    if (moveFocus.current) control.current?.focus();
    moveFocus.current = false;
  }, [timer]);

  // Another tab started or stopped the timer.
  useEffect(() => {
    const onStorage = (e) => e.key === KEY && setTimer(settle(readTimer(), Date.now()));
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  useEffect(() => {
    if (!timer) return;
    const id = setInterval(() => {
      const at = Date.now();
      setNow(at);
      const next = settle(timer, at);
      if (next === timer) return;
      setTimer(next);
      setNotice(
        next
          ? `Fim do foco. Pausa de ${timer.breakMinutes} min.`
          : timer.phase === "break"
            ? "Fim da pausa."
            : "Fim do foco.",
      );
    }, 1000);
    return () => clearInterval(id);
  }, [timer]);

  async function start() {
    setStarting(true);
    setError(null);
    try {
      // Read at each start, so a duration saved in Configurações counts from the next focus.
      const settings = await api.get("/api/settings/");
      const at = Date.now();
      setNow(at);
      setNotice(null);
      moveFocus.current = true;
      setTimer({
        phase: "focus",
        endsAt: at + settings.pomodoro_focus_minutes * MINUTE,
        breakMinutes: settings.pomodoro_break_minutes,
      });
    } catch (e) {
      setError(`Não foi possível ler as durações. ${e.message}`);
    }
    setStarting(false);
  }

  return (
    <section className="pomodoro" aria-labelledby="pomodoro-title">
      <h2 className="pomodoro__title" id="pomodoro-title">
        <Icon name="clock" />
        Pomodoro
      </h2>
      {timer ? (
        <div className="pomodoro__running">
          <p className="pomodoro__phase">
            {timer.phase === "focus" ? "Foco" : "Pausa"}
            {/* Read on demand, not announced every second. */}
            <span className="pomodoro__time">{clock(timer.endsAt - now)}</span>
          </p>
          <Button
            ref={control}
            variant="tertiary"
            onClick={() => {
              moveFocus.current = true;
              setTimer(null);
            }}
          >
            Parar
          </Button>
        </div>
      ) : (
        <Button ref={control} variant="tertiary" loading={starting} loadingLabel="Iniciando…" onClick={start}>
          Iniciar foco
        </Button>
      )}
      {error && (
        <p className="pomodoro__error" role="alert">
          {error}
        </p>
      )}
      {createPortal(
        // The live region stays in the page, so a notice placed in it is announced.
        <div className="pomodoro-notice" role="status" data-print="hide">
          {notice && (
            <div className="pomodoro-notice__body">
              <Icon name="clock" />
              <p>{notice}</p>
              <button
                type="button"
                className="pomodoro-notice__close"
                aria-label="Fechar aviso do pomodoro"
                onClick={() => setNotice(null)}
              >
                <Icon name="close" />
              </button>
            </div>
          )}
        </div>,
        document.body,
      )}
    </section>
  );
}
