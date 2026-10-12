import { useEffect, useState } from "react";

export default function App() {
  const [api, setApi] = useState("verificando");

  useEffect(() => {
    fetch("/api/health/")
      .then((r) => (r.ok ? "ok" : "erro"))
      .catch(() => "erro")
      .then(setApi);
  }, []);

  return (
    <main>
      <h1>Athenas</h1>
      <p>API: {api}</p>
    </main>
  );
}
