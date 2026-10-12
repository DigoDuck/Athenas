import { useCallback, useEffect, useState } from "react";

import { api } from "./api.js";

const fetchAll = (key) => Promise.all(key.split("|").map((url) => api.get(url)));

// Loads several list endpoints together and exposes a reload.
export function useCollections(urls) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const key = urls.join("|");

  useEffect(() => {
    let active = true;
    fetchAll(key).then(
      (lists) => active && setData(lists),
      (e) => active && setError(e.message),
    );
    return () => {
      active = false;
    };
  }, [key]);

  const reload = useCallback(async () => {
    try {
      setData(await fetchAll(key));
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  }, [key]);

  return { data, error, reload };
}
