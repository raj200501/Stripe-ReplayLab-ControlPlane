import { useEffect, useState } from 'react'

export function useFetch<T>(loader: () => Promise<T>, deps: unknown[] = []) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<T | null>(null)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    loader()
      .then((next) => {
        if (!mounted) return
        setData(next)
        setError(null)
      })
      .catch((err) => {
        if (!mounted) return
        setError(String(err))
      })
      .finally(() => mounted && setLoading(false))
    return () => {
      mounted = false
    }
  }, deps)

  return { loading, error, data }
}
