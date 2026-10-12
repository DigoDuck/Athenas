import { useState } from "react";

// One text field and a button. Clears itself after a successful submit.
export default function InlineForm({ placeholder, button, onSubmit }) {
  const [value, setValue] = useState("");

  async function submit(event) {
    event.preventDefault();
    const name = value.trim();
    if (!name) return;
    if (await onSubmit(name)) setValue("");
  }

  return (
    <form className="inline-form" onSubmit={submit}>
      <input value={value} onChange={(e) => setValue(e.target.value)} placeholder={placeholder} />
      <button type="submit">{button}</button>
    </form>
  );
}
