import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Runs an async function on mount (and whenever `deps` change), tracking
 * loading/error/data. Returns `reload` so callers can refetch after a
 * mutation. Guards against setting state on an unmounted component and
 * against a slow earlier request overwriting a newer one.
 */
export function useAsync(fn, deps = []) {
  const [state, setState] = useState({ data: null, error: '', loading: true })
  const runId = useRef(0)
  const alive = useRef(true)

  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
    }
  }, [])

  const run = useCallback(async () => {
    const id = ++runId.current
    setState((s) => ({ ...s, loading: true, error: '' }))
    try {
      const data = await fn()
      if (alive.current && id === runId.current) {
        setState({ data, error: '', loading: false })
      }
    } catch (err) {
      if (alive.current && id === runId.current) {
        setState({ data: null, error: err.message, loading: false })
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    run()
  }, [run])

  return { ...state, reload: run }
}
