import { useEffect, useState } from "react";

import { api } from "../api.js";
import { Button, Callout, Stack, StateMessage } from "../ui/index.js";
import { ActionError } from "./forms.jsx";

// The app suggests, Diogo decides (spec 4.4.2, DECISIONS.md D-024). The server owns the criteria,
// so this asks it each time it mounts; remount it with a new key after anything that may count.
export default function CompletionSuggestion({ subtopicId }) {
  const [suggested, setSuggested] = useState(false);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    // Optional help: if the check fails, the screen simply goes without it.
    api.get(`/api/subtopics/${subtopicId}/`).then(
      (s) => active && setSuggested(s.completion_suggested),
      () => {},
    );
    return () => {
      active = false;
    };
  }, [subtopicId]);

  async function complete() {
    setBusy(true);
    setError(null);
    try {
      await api.post(`/api/subtopics/${subtopicId}/complete/`);
      setDone(true);
    } catch (e) {
      setError(`Não foi possível concluir. ${e.message}`);
    }
    setBusy(false);
  }

  if (done) {
    return (
      <div role="status">
        <StateMessage kind="success" title="Subtema concluído.">
          Os cartões dele continuam na revisão. Se mudar de ideia, reabra na Biblioteca.
        </StateMessage>
      </div>
    );
  }
  if (!suggested) return null;
  return (
    <Callout variant="info" title="Este subtema pode ser concluído">
      <Stack gap={3}>
        <p>
          Você leu todos os blocos e tem uma tentativa certa ou parcial. Concluir encerra este ciclo
          de estudo; a decisão é sua.
        </p>
        <ActionError>{error}</ActionError>
        <div>
          <Button icon="check-circle" loading={busy} loadingLabel="Concluindo…" onClick={complete}>
            Concluir subtema
          </Button>
        </div>
      </Stack>
    </Callout>
  );
}
