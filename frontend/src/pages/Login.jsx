import { useState } from "react";

import { api } from "../api.js";
import { Brand, Button, Panel, Stack, TextField } from "../ui/index.js";
import "./login.css";

// Sign-in (DECISIONS.md D-044). Accounts are created by Diogo in the admin; there is no sign-up.
export default function Login({ onSignedIn }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [sending, setSending] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setSending(true);
    setError(null);
    try {
      onSignedIn(await api.post("/api/auth/login/", { username, password }));
    } catch (err) {
      setError(err.message);
      setSending(false);
    }
  }

  return (
    <main className="login">
      <Panel className="login__panel" raised>
        <Brand />
        <form onSubmit={submit}>
          <Stack>
            <h1 className="t-section-title">Entrar</h1>
            <TextField
              label="Usuário"
              name="username"
              autoComplete="username"
              autoCapitalize="none"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <TextField
              label="Senha"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              error={error}
              onChange={(e) => setPassword(e.target.value)}
            />
            <Button type="submit" loading={sending} loadingLabel="Entrando…">
              Entrar
            </Button>
          </Stack>
        </form>
      </Panel>
    </main>
  );
}
