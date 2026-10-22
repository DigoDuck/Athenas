import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { api } from "../api.js";
import { Button, Icon } from "../ui/index.js";
import "./pomodoro.css";

// Pomodoro (spec 4.9, DECISIONS.md D-037). An end time in localStorage, not a countdown, so the
// timer survives a reload and stays right in a throttled background tab.

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

// The break counts from the focus's end, not from when a tick noticed it.
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

  const current = useRef(timer);
  useEffect(() => {
    current.current = timer;
  }, [timer]);

  // Only a change made here is written: echoing one adopted from another tab could undo a
  // newer one made there.
  function change(next) {
    writeTimer(next);
    setTimer(next);
  }

  useEffect(() => {
    function onStorage(e) {
      if (e.key !== KEY) return;
      const at = Date.now();
      const stored = settle(readTimer(), at);
      const own = settle(current.current, at);
      // Another tab settled the phase this tab settles on its next tick: that tick gives the notice.
      if (stored?.phase === own?.phase && stored?.endsAt === own?.endsAt) return;
      setNow(at);
      setTimer(stored);
    }
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
      change(next);
      // Without a next phase the break is over, even when a sleep skipped it whole.
      setNotice(next ? `Fim do foco. Pausa de ${timer.breakMinutes} min.` : "Fim da pausa.");
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
      change({
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
      <div className="pomodoro__row">
        {timer && (
          <p className="pomodoro__phase">
            {timer.phase === "focus" ? "Foco" : "Pausa"}
            {/* Read on demand, not announced every second. */}
            <span className="pomodoro__time">{clock(timer.endsAt - now)}</span>
          </p>
        )}
        {/* One button that changes its label, so the focus stays on it when the timer starts or ends. */}
        <Button
          variant="tertiary"
          loading={timer ? undefined : starting}
          loadingLabel="Iniciando…"
          onClick={timer ? () => change(null) : start}
        >
          {timer ? "Parar" : "Iniciar foco"}
        </Button>
      </div>
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
