import { useState } from "react";

import { Button, Inline, TextField } from "../ui/index.js";

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
    <Inline as="form" align="end" onSubmit={submit}>
      <TextField label={label} value={value} error={error} onChange={(e) => setValue(e.target.value)} />
      <Button type="submit" variant="secondary" loading={saving} loadingLabel="Adicionando…">
        {button}
      </Button>
    </Inline>
  );
}

// [[value, label], ...] as the options the Select base component takes.
export const toOptions = (pairs) => pairs.map(([value, label]) => ({ value, label }));
