"use client"

import { useEffect, useState, useRef } from "react"
import { useParams } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import LogFeed from "../components/log-feed"
import PaperDisplay from "../components/paper-display"
import IdeaDisplay from "../components/idea-display"
import ExperimentResultDisplay from "../components/result-display"

interface ExperimentState {
  status: string
  current_stage: string
  papers: any[]
  ideas: any[]
  results: any[]
}

export default function ExperimentPage() {
  const params = useParams()
  const jobId = params.job_id as string
  const [state, setState] = useState<ExperimentState>({
    status: "initializing",
    current_stage: "setup",
    papers: [],
    ideas: [],
    results: [],
  })
  const [logs, setLogs] = useState<string[]>([])
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const token = localStorage.getItem("auth_token")
    const wsUrl = `${process.env.NEXT_PUBLIC_API_URL?.replace("http", "ws")}/ws/${jobId}?token=${token}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)

      if (message.type === "log") {
        setLogs((prev) => [...prev, message.content])
      } else if (message.type === "state_update") {
        setState((prev) => ({
          ...prev,
          ...message.state,
        }))
      } else if (message.type === "paper") {
        setState((prev) => ({
          ...prev,
          papers: [...prev.papers, message.data],
        }))
      } else if (message.type === "idea") {
        setState((prev) => ({
          ...prev,
          ideas: [...prev.ideas, message.data],
        }))
      } else if (message.type === "result") {
        setState((prev) => ({
          ...prev,
          results: [...prev.results, message.data],
        }))
      }
    }

    return () => {
      ws.close()
    }
  }, [jobId])

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Experiment Monitor</h1>
        <div className="flex items-center gap-4">
          <div
            className={`px-3 py-1 rounded-full text-sm font-semibold ${
              state.status === "running"
                ? "bg-green-500/20 text-green-300"
                : state.status === "completed"
                  ? "bg-blue-500/20 text-blue-300"
                  : "bg-yellow-500/20 text-yellow-300"
            }`}
          >
            {state.status.charAt(0).toUpperCase() + state.status.slice(1)}
          </div>
          <span className="text-gray-400">Stage: {state.current_stage}</span>
        </div>
      </div>

      <Tabs defaultValue="logs" className="space-y-4">
        <TabsList className="bg-white/10 border-white/10">
          <TabsTrigger value="logs">Live Logs</TabsTrigger>
          <TabsTrigger value="papers">Papers ({state.papers.length})</TabsTrigger>
          <TabsTrigger value="ideas">Ideas ({state.ideas.length})</TabsTrigger>
          <TabsTrigger value="results">Results ({state.results.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="logs">
          <Card className="bg-white/5 border-white/10 backdrop-blur p-6">
            <LogFeed logs={logs} />
          </Card>
        </TabsContent>

        <TabsContent value="papers">
          <div className="grid gap-4">
            {state.papers.length === 0 ? (
              <Card className="bg-white/5 border-white/10 backdrop-blur p-6 text-center text-gray-400">
                No papers discovered yet
              </Card>
            ) : (
              state.papers.map((paper, idx) => <PaperDisplay key={idx} paper={paper} />)
            )}
          </div>
        </TabsContent>

        <TabsContent value="ideas">
          <div className="grid gap-4">
            {state.ideas.length === 0 ? (
              <Card className="bg-white/5 border-white/10 backdrop-blur p-6 text-center text-gray-400">
                No ideas generated yet
              </Card>
            ) : (
              state.ideas.map((idea, idx) => <IdeaDisplay key={idx} idea={idea} />)
            )}
          </div>
        </TabsContent>

        <TabsContent value="results">
          <div className="grid gap-4">
            {state.results.length === 0 ? (
              <Card className="bg-white/5 border-white/10 backdrop-blur p-6 text-center text-gray-400">
                No results yet
              </Card>
            ) : (
              state.results.map((result, idx) => <ExperimentResultDisplay key={idx} result={result} />)
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
