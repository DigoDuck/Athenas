import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../api.js";
import { Button, Inline, Panel, StateMessage, TextField } from "../ui/index.js";
import "./settings.css";

// Configurações (spec 3.2, DECISIONS.md D-037). The API checks the bounds and names the field.

const GROUPS = [
  {
    legend: "Revisões",
    fields: [
      {
        name: "review_cap",
        label: "Revisões por dia",
        help: "Conta cada cartão uma vez por dia, com os novos incluídos. De 1 a 200.",
        min: 1,
        max: 200,
      },
      {
        name: "new_card_cap",
        label: "Cartões novos por dia",
        help: "Entram dentro das revisões do dia. Com 0, nenhum cartão novo entra.",
        min: 0,
        max: 200,
      },
      {
        name: "desired_retention",
        label: "Retenção desejada (%)",
        help:
          "A chance de lembrar que o agendamento busca: mais alta traz revisões mais próximas. " +
          "Vale a partir da próxima avaliação de cada cartão. De 70 a 97.",
        min: 70,
        max: 97,
      },
    ],
  },
  {
    legend: "Pomodoro",
    fields: [
      {
        name: "pomodoro_focus_minutes",
        label: "Foco (minutos)",
        help: "Vale a partir do próximo foco. De 1 a 180.",
        min: 1,
        max: 180,
      },
      {
        name: "pomodoro_break_minutes",
        label: "Pausa (minutos)",
        help: "Começa sozinha quando o foco termina. De 1 a 60.",
        min: 1,
        max: 60,
      },
    ],
  },
];

const toForm = (data) => ({
  ...Object.fromEntries(Object.entries(data).map(([key, value]) => [key, String(value)])),
  desired_retention: String(Math.round(data.desired_retention * 100)),
});

// Whole percentages only, so the value stored is the one the field shows after the save. An
// empty or unreadable field goes as "", so the API answers with its own message.
const toApi = (form) => ({
  ...form,
  desired_retention: form.desired_retention === "" ? "" : Math.round(Number(form.desired_retention)) / 100,
});

export default function Settings() {
  const [form, setForm] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState(null);
  const formRef = useRef(null);
  const focusError = useRef(false);

  // After a refused save, the first field marked wrong takes the focus.
  useEffect(() => {
    if (focusError.current) formRef.current?.querySelector("[aria-invalid]")?.focus();
    focusError.current = false;
  }, [errors]);

  const load = useCallback(
    () =>
      api.get("/api/settings/").then(
        (data) => {
          setForm(toForm(data));
          setLoadError(null);
        },
        setLoadError,
      ),
    [],
  );

  useEffect(() => {
    load();
  }, [load]);

  function change(name, value) {
    setForm({ ...form, [name]: value });
    setErrors({ ...errors, [name]: undefined });
    setStatus(null);
  }

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setStatus(null);
    try {
      setForm(toForm(await api.patch("/api/settings/", toApi(form))));
      setErrors({});
      setStatus({ kind: "saved", text: "Configurações salvas." });
    } catch (e) {
      const fields = e.status === 400 && e.data ? e.data : {};
      focusError.current = true;
      setErrors(Object.fromEntries(Object.entries(fields).map(([key, value]) => [key, [value].flat().join(" ")])));
      setStatus({
        kind: "error",
        text: Object.keys(fields).length ? "Nada foi salvo. Confira os campos marcados." : `Nada foi salvo. ${e.message}`,
      });
    }
    setSaving(false);
  }

  return (
    <div className="settings">
      <header className="settings__head">
        <h1>Configurações</h1>
      </header>
      {loadError ? (
        <StateMessage
          kind="error"
          title="Não foi possível carregar as configurações."
          action={<Button onClick={load}>Tentar novamente</Button>}
        >
          {loadError.message}
        </StateMessage>
      ) : !form ? (
        <p className="t-meta">Carregando…</p>
      ) : (
        <Panel as="form" ref={formRef} className="settings__form" noValidate onSubmit={submit}>
          {GROUPS.map((group) => (
            <fieldset key={group.legend} className="settings__group">
              <legend className="t-section-title">{group.legend}</legend>
              {group.fields.map((field) => (
                <TextField
                  key={field.name}
                  label={field.label}
                  help={field.help}
                  error={errors[field.name]}
                  type="number"
                  inputMode="numeric"
                  min={field.min}
                  max={field.max}
                  step={1}
                  value={form[field.name]}
                  onChange={(e) => change(field.name, e.target.value)}
                />
              ))}
            </fieldset>
          ))}
          <Inline gap={4} className="settings__actions">
            <Button type="submit" loading={saving}>
              Salvar
            </Button>
            {/* Present before any text, so the result is announced when it appears. */}
            <p className="settings__status" role="status" data-kind={status?.kind}>
              {status?.text}
            </p>
          </Inline>
        </Panel>
      )}
    </div>
  );
}
