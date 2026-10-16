import { useEffect, useState } from "react";

import Library from "./pages/Library.jsx";
import Roadmap from "./pages/Roadmap.jsx";
import Study from "./pages/Study.jsx";
import { AppShell } from "./ui/index.js";

const PAGES = {
  roadmap: { label: "Roadmap", icon: "roadmap", Component: Roadmap },
  biblioteca: { label: "Biblioteca", icon: "library", Component: Library },
};

const NAV_ITEMS = Object.entries(PAGES).map(([id, { label, icon }]) => ({
  id,
  label,
  icon,
  href: `#/${id}`,
}));

// "#/estudo/<subtopic id>" is the reading screen; the nav keeps Biblioteca marked.
function currentRoute() {
  const [key, id] = window.location.hash.replace("#/", "").split("/");
  if (key === "estudo" && /^\d+$/.test(id ?? "")) return { page: "biblioteca", study: Number(id) };
  return { page: key in PAGES ? key : "roadmap" };
}

export default function App() {
  const [route, setRoute] = useState(currentRoute);

  useEffect(() => {
    const onHashChange = () => setRoute(currentRoute());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const { Component } = PAGES[route.page];

  return (
    <AppShell items={NAV_ITEMS} current={route.page}>
      {route.study ? <Study key={route.study} subtopicId={route.study} /> : <Component />}
    </AppShell>
  );
}
