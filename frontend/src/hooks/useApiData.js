import { useCallback, useEffect, useState } from "react";

export default function useApiData(loader, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const load = useCallback(loader, deps);

  useEffect(() => {
    let cancelled = false;
    setState({ data: null, error: null, loading: true });
    load()
      .then((data) => !cancelled && setState({ data, error: null, loading: false }))
      .catch(
        (error) =>
          !cancelled && setState({ data: null, error: error.message, loading: false })
      );
    return () => {
      cancelled = true;
    };
  }, [load]);

  return state;
}
