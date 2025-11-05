"use client"

import { useEffect, useState } from "react"

export function useAuth() {
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const storedToken = localStorage.getItem("auth_token")
    setToken(storedToken)
    setLoading(false)
  }, [])

  return { token, loading }
}
