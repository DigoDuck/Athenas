import { useId, useState } from "react";

import { Button, TextField } from "../ui/index.js";

// A labelled text field and one button. Clears itself after a successful submit and shows
// the API's message on the field when it fails.
export function NameForm({ label, button, onSubmit }) {
  const [value, setValue] = useState("");
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  async function submit(event) {
    event.preventDefault();
    const name = value.trim();
    if (!name) {
      setError(`Informe o ${label.toLowerCase()}.`);
      return;
    }
    setSaving(true);
    const failure = await onSubmit(name);
    setSaving(false);
    setError(failure);
    if (!failure) setValue("");
  }

  return (
    <form onSubmit={submit}>
      <TextField label={label} value={value} error={error} onChange={(e) => setValue(e.target.value)} />
      <Button type="submit" variant="secondary" loading={saving} loadingLabel="Adicionando…">
        {button}
      </Button>
    </form>
  );
}

// Native select with the base field classes. There is no Select base component yet.
export function SelectField({ label, value, options, onChange }) {
  const id = useId();
  return (
    <div className="ui-field">
      <label className="ui-field__label" htmlFor={id}>
        {label}
      </label>
      <select id={id} className="ui-input" value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map(([v, text]) => (
          <option key={v} value={v}>
            {text}
          </option>
        ))}
      </select>
    </div>
  );
}
