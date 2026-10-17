import { useEffect, useRef, useState } from "react";

import { Button, Icon, Inline, TextField } from "../ui/index.js";
import "./forms.css";

// A labelled text field and one button. Clears itself after a successful submit and shows
// the API's message on the field when it fails. `onCancel` adds a "Cancelar" button and Esc.
export function NameForm({ label, button, loadingLabel = "Adicionando…", autoFocus, onSubmit, onCancel }) {
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
    <Inline
      as="form"
      align="end"
      className="field-row"
      onSubmit={submit}
      onKeyDown={onCancel && ((e) => e.key === "Escape" && onCancel())}
    >
      <TextField
        label={label}
        value={value}
        error={error}
        autoFocus={autoFocus}
        onChange={(e) => setValue(e.target.value)}
      />
      <Button type="submit" variant="secondary" loading={saving} loadingLabel={loadingLabel}>
        {button}
      </Button>
      {onCancel && (
        <Button variant="tertiary" onClick={onCancel}>
          Cancelar
        </Button>
      )}
    </Inline>
  );
}

// A "+ button" that opens a NameForm in its place, so empty forms do not fill the page.
// The form stays open after each add, for several names in a row; closing it hands focus back.
export function AddForm({ variant = "tertiary", ...form }) {
  const [open, setOpen] = useState(false);
  const trigger = useRef(null);
  const wasOpen = useRef(open);

  useEffect(() => {
    if (wasOpen.current && !open) trigger.current?.focus();
    wasOpen.current = open;
  }, [open]);

  if (open) return <NameForm {...form} autoFocus onCancel={() => setOpen(false)} />;
  return (
    <Button
      ref={trigger}
      variant={variant}
      icon="plus"
      className="add-form__trigger"
      onClick={() => setOpen(true)}
    >
      {form.button}
    </Button>
  );
}

// A failed action, shown inside the section it came from instead of at the top of the page.
// Same look as a field error; renders nothing when there is no message.
export function ActionError({ children }) {
  if (!children) return null;
  return (
    <p className="ui-field__error" role="alert">
      <Icon name="alert-circle" />
      {children}
    </p>
  );
}

// [[value, label], ...] as the options the Select base component takes.
export const toOptions = (pairs) => pairs.map(([value, label]) => ({ value, label }));
