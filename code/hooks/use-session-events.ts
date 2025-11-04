import { useEffect, useMemo, useRef, useState } from "react"

import { API_BASE_URL } from "@/lib/api-client"

export interface SessionEventPayload {
  timestamp: string
  stage: string
  message: string
  metadata?: Record<string, unknown>
}

type StreamState = "idle" | "connecting" | "open" | "closed" | "error"

function normaliseEvent(event: SessionEventPayload): SessionEventPayload {
  return {
    ...event,
    metadata: event.metadata ?? {},
  }
}

export function useSessionEvents(sessionId: string | null | undefined) {
  const [events, setEvents] = useState<SessionEventPayload[]>([])
  const [state, setState] = useState<StreamState>("idle")
  const controllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    if (!sessionId) {
      setEvents([])
      if (controllerRef.current) {
        controllerRef.current.abort()
      }
      setState("idle")
      return
    }

    const controller = new AbortController()
    controllerRef.current = controller
    setState("connecting")

    const streamEvents = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/events/stream`, {
          signal: controller.signal,
        })
        if (!response.body) {
          setState("error")
          return
        }
        setState("open")
        const reader = response.body.getReader()
        const decoder = new TextDecoder("utf-8")
        let buffer = ""

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })

          let boundary = buffer.indexOf("\n\n")
          while (boundary !== -1) {
            const chunk = buffer.slice(0, boundary)
            buffer = buffer.slice(boundary + 2)
            if (chunk.startsWith("data:")) {
              const payload = chunk.replace(/^data:\s*/, "").trim()
              if (payload) {
                try {
                  const parsed = JSON.parse(payload)
                  setEvents((prev) => [...prev, normaliseEvent(parsed)])
                } catch (error) {
                  console.warn("Failed to parse session event", error)
                }
              }
            }
            boundary = buffer.indexOf("\n\n")
          }
        }
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          console.warn("Session event stream failed", error)
          setState("error")
        }
      } finally {
        setState((prev) => (prev === "error" ? prev : "closed"))
      }
    }

    streamEvents()

    return () => {
      controller.abort()
      controllerRef.current = null
    }
  }, [sessionId])

  const groupedByStage = useMemo(() => {
    return events.reduce<Record<string, SessionEventPayload[]>>((acc, event) => {
      const key = event.stage
      if (!acc[key]) {
        acc[key] = []
      }
      acc[key].push(event)
      return acc
    }, {})
  }, [events])

  return { events, groupedByStage, state }
}

export type SessionEventStreamState = ReturnType<typeof useSessionEvents>["state"]