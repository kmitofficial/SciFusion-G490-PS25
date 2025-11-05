"use client"

import { useEffect, useRef } from "react"

interface LogFeedProps {
  logs: string[]
}

export default function LogFeed({ logs }: LogFeedProps) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [logs])

  return (
    <div className="bg-black/40 rounded-lg p-4 font-mono text-sm max-h-96 overflow-y-auto">
      {logs.length === 0 ? (
        <div className="text-gray-500">Waiting for logs...</div>
      ) : (
        logs.map((log, idx) => (
          <div key={idx} className="text-gray-300 mb-1">
            <span className="text-gray-600">[{idx}]</span> {log}
          </div>
        ))
      )}
      <div ref={endRef} />
    </div>
  )
}
