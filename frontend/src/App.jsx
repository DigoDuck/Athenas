import { useEffect, useState } from "react";

import Home from "./pages/Home.jsx";
import Library from "./pages/Library.jsx";
import Login from "./pages/Login.jsx";
import NewTheme from "./pages/NewTheme.jsx";
import Notebook from "./pages/Notebook.jsx";
import Pomodoro from "./pages/Pomodoro.jsx";
import Practice from "./pages/Practice.jsx";
import Review from "./pages/Review.jsx";
import Roadmap from "./pages/Roadmap.jsx";
import Settings from "./pages/Settings.jsx";
import Study from "./pages/Study.jsx";
import { api } from "./api.js";
import { AppShell, Button, StateMessage } from "./ui/index.js";

const PAGES = {
  inicio: { label: "Início", icon: "home", Component: Home },
  roadmap: { label: "Roadmap", icon: "roadmap", Component: Roadmap },
  biblioteca: { label: "Biblioteca", icon: "library", Component: Library },
  revisoes: { label: "Revisões", icon: "reviews", Component: Review },
  "novo-tema": { label: "Novo tema", icon: "plus", Component: NewTheme },
};

// Configurações is a secondary action at the foot of the navigation (design system 4).
const SECONDARY_PAGES = {
  configuracoes: { label: "Configurações", icon: "settings", Component: Settings },
};

const ALL_PAGES = { ...PAGES, ...SECONDARY_PAGES };

const navItems = (pages) =>
  Object.entries(pages).map(([id, { label, icon }]) => ({ id, label, icon, href: `#/${id}` }));
const NAV_ITEMS = navItems(PAGES);
const SECONDARY_NAV_ITEMS = navItems(SECONDARY_PAGES);

// The screens that open the day get a panorama each; the rest stay on plain marble.
const SCENES = { inicio: "home", roadmap: "roadmap" };

// "#/estudo/<subtopic id>" is reading, "#/caderno/<subtopic id>" notebook mode and
// "#/pratica/<subtopic id>" practice; the nav keeps Biblioteca marked. "#/roadmap/<track id>"
// opens the Roadmap on that track.
const SUBTOPIC_PAGES = { estudo: Study, caderno: Notebook, pratica: Practice };

function currentRoute() {
  const [key, id] = window.location.hash.replace("#/", "").split("/");
  if (key in SUBTOPIC_PAGES && /^\d+$/.test(id ?? "")) {
    return { page: "biblioteca", Subpage: SUBTOPIC_PAGES[key], subtopic: Number(id), key };
  }
  return {
    page: Object.hasOwn(ALL_PAGES, key) ? key : "inicio",
    id: /^\d+$/.test(id ?? "") ? Number(id) : null,
  };
}

// Who is signed in: undefined while asking, null for nobody, an Error when the API is down.
function useSession() {
  const [user, setUser] = useState(undefined);
  const fetchUser = () =>
    api
      .get("/api/auth/me/")
      .then(setUser)
      .catch((error) => setUser(error.status === 403 ? null : error));
  useEffect(() => {
    fetchUser();
  }, []);
  const ask = () => {
    setUser(undefined);
    fetchUser();
  };
  return { user, setUser, ask };
}

export default function App() {
  const { user, setUser, ask } = useSession();
  if (user === undefined) return null;
  if (user instanceof Error) {
    return (
      <main className="login">
        <StateMessage
          kind="error"
          title="Não foi possível abrir o Athenas."
          action={<Button onClick={ask}>Tentar de novo</Button>}
        >
          {user.message}
        </StateMessage>
      </main>
    );
  }
  if (user === null) return <Login onSignedIn={setUser} />;
  return <SignedIn />;
}

function SignedIn() {
  const [route, setRoute] = useState(currentRoute);

  useEffect(() => {
    const onHashChange = () => setRoute(currentRoute());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const { Component } = ALL_PAGES[route.page];

  // A full reload after leaving drops every screen's state, so nothing of this session lingers.
  const signOut = () => api.post("/api/auth/logout/").finally(() => window.location.reload());

  return (
    <AppShell
      items={NAV_ITEMS}
      secondaryItems={SECONDARY_NAV_ITEMS}
      navFooter={
        <>
          <Pomodoro />
          <Button variant="tertiary" onClick={signOut}>
            Sair
          </Button>
        </>
      }
      current={route.page}
      scene={route.Subpage ? null : (SCENES[route.page] ?? null)}
    >
      {route.Subpage ? (
        <route.Subpage key={`${route.key}/${route.subtopic}`} subtopicId={route.subtopic} />
      ) : (
        <Component key={route.id} trackId={route.id} />
      )}
    </AppShell>
  );
}
