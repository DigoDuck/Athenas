import { useEffect, useState } from "react";

import Home from "./pages/Home.jsx";
import Library from "./pages/Library.jsx";
import Practice from "./pages/Practice.jsx";
import Review from "./pages/Review.jsx";
import Roadmap from "./pages/Roadmap.jsx";
import Study from "./pages/Study.jsx";
import { AppShell } from "./ui/index.js";

const PAGES = {
  inicio: { label: "Início", icon: "home", Component: Home },
  roadmap: { label: "Roadmap", icon: "roadmap", Component: Roadmap },
  biblioteca: { label: "Biblioteca", icon: "library", Component: Library },
  revisoes: { label: "Revisões", icon: "reviews", Component: Review },
};

const NAV_ITEMS = Object.entries(PAGES).map(([id, { label, icon }]) => ({
  id,
  label,
  icon,
  href: `#/${id}`,
}));

// The screens that open the day get a panorama each; the rest stay on plain marble.
const SCENES = { inicio: "home", roadmap: "roadmap" };

// "#/estudo/<subtopic id>" is reading and "#/pratica/<subtopic id>" practice; the nav keeps
// Biblioteca marked.
const SUBTOPIC_PAGES = { estudo: Study, pratica: Practice };

function currentRoute() {
  const [key, id] = window.location.hash.replace("#/", "").split("/");
  if (key in SUBTOPIC_PAGES && /^\d+$/.test(id ?? "")) {
    return { page: "biblioteca", Subpage: SUBTOPIC_PAGES[key], subtopic: Number(id), key };
  }
  return { page: key in PAGES ? key : "inicio" };
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
    <AppShell items={NAV_ITEMS} current={route.page} scene={route.Subpage ? null : (SCENES[route.page] ?? null)}>
      {route.Subpage ? (
        <route.Subpage key={`${route.key}/${route.subtopic}`} subtopicId={route.subtopic} />
      ) : (
        <Component />
      )}
    </AppShell>
  );
}
