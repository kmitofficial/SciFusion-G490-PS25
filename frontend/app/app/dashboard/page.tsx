"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card } from "@/components/ui/card"
import { useToast } from "@/hooks/use-toast"
import { Checkbox } from "@/components/ui/checkbox"

const MODELS = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet"]

export default function DashboardPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [topic, setTopic] = useState("")
  const [model, setModel] = useState(MODELS[0])
  const [useRag, setUseRag] = useState(true)
  const [checkNovelty, setCheckNovelty] = useState(true)
  const [loading, setLoading] = useState(false)

  const handleStartExperiment = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const token = localStorage.getItem("auth_token")
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/experiments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          topic,
          model,
          use_rag: useRag,
          check_novelty: checkNovelty,
        }),
      })

      if (!response.ok) {
        throw new Error("Failed to start experiment")
      }

      const data = await response.json()
      router.push(`/app/experiment/${data.job_id}`)
    } catch (error) {
      toast({ title: "Error", description: "Failed to start experiment", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8">
      <div className="max-w-2xl">
        <h1 className="text-4xl font-bold mb-2">Create New Experiment</h1>
        <p className="text-gray-400 mb-8">Configure and launch a new research automation experiment</p>

        <Card className="bg-white/5 border-white/10 backdrop-blur">
          <form onSubmit={handleStartExperiment} className="p-8 space-y-6">
            <div>
              <Label htmlFor="topic" className="text-white">
                Research Topic
              </Label>
              <Input
                id="topic"
                placeholder="e.g., Recent advances in quantum machine learning"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="mt-2 bg-white/10 border-white/20 text-white placeholder:text-gray-500"
                required
              />
            </div>

            <div>
              <Label htmlFor="model" className="text-white">
                AI Model
              </Label>
              <select
                id="model"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="mt-2 w-full px-4 py-2 bg-white/10 border border-white/20 text-white rounded-md"
              >
                {MODELS.map((m) => (
                  <option key={m} value={m} className="bg-black text-white">
                    {m}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="rag"
                  checked={useRag}
                  onCheckedChange={(checked) => setUseRag(checked as boolean)}
                  className="border-white/20"
                />
                <Label htmlFor="rag" className="text-white cursor-pointer">
                  Use RAG (Retrieval Augmented Generation)
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="novelty"
                  checked={checkNovelty}
                  onCheckedChange={(checked) => setCheckNovelty(checked as boolean)}
                  className="border-white/20"
                />
                <Label htmlFor="novelty" className="text-white cursor-pointer">
                  Check Novelty of Results
                </Label>
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading || !topic}
              className="w-full bg-white text-black hover:bg-white/90 py-6 text-base font-semibold"
            >
              {loading ? "Starting..." : "Start Experiment"}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  )
}
