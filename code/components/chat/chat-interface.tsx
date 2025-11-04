"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, Loader2, Menu, Settings2 } from "lucide-react"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

interface ChatInterfaceProps {
  conversationId: string | null
  onToggleSidebar: () => void
  isSidebarOpen: boolean
}

export function ChatInterface({ conversationId, onToggleSidebar, isSidebarOpen }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Welcome to Scifusion! I'm your AI-powered research assistant. I can help you generate research hypotheses, validate experiments, provide domain-specific insights in bioinformatics, materials science, environmental modeling, and more. What research challenge can I help you explore today?",
      timestamp: new Date(),
    },
  ])
  const [inputValue, setInputValue] = useState("")
  const [numIdeas, setNumIdeas] = useState("5")
  const [maxPapers, setMaxPapers] = useState("10")
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: String(messages.length + 1),
      role: "user",
      content: inputValue,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setIsLoading(true)

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: [
            ...messages.map((msg) => ({
              role: msg.role,
              content: msg.content,
            })),
            {
              role: "user",
              content: inputValue,
            },
          ],
          numIdeas: Number.parseInt(numIdeas),
          maxPapers: Number.parseInt(maxPapers),
        }),
      })

      if (!response.ok) {
        throw new Error("Failed to get response from AI")
      }

      const data = await response.json()

      const assistantMessage: Message = {
        id: String(messages.length + 2),
        role: "assistant",
        content: data.content,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to get AI response"
      const errorAssistantMessage: Message = {
        id: String(messages.length + 2),
        role: "assistant",
        content: `Sorry, I encountered an error: ${errorMessage}. Please try again.`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorAssistantMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Top Bar */}
      <div className="flex items-center justify-between h-16 px-4 md:px-6 border-b border-white/10 bg-background">
        <div className="flex items-center gap-2">
          <button onClick={onToggleSidebar} className="md:hidden p-2 hover:bg-white/10 rounded-lg transition-colors">
            <Menu className="h-5 w-5 text-foreground" />
          </button>
          <h1 className="text-lg font-semibold text-foreground hidden md:block">Scifusion</h1>
        </div>
        <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
          <Settings2 className="h-5 w-5 text-foreground" />
        </button>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
        {messages.length === 1 && messages[0].role === "assistant" ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-full max-w-2xl space-y-6">
              {/* Welcome Message */}
              <div className="text-center mb-8">
                <div className="mb-4 w-20 h-20 rounded-full bg-gradient-to-br from-teal-500/20 to-cyan-600/20 flex items-center justify-center border border-teal-500/30 mx-auto">
                  <span className="text-4xl">🔬</span>
                </div>
                <h2 className="text-3xl font-bold text-foreground mb-2">What research question can I help with?</h2>
                <p className="text-muted-foreground">
                  Generate novel hypotheses, validate experiments, and accelerate your scientific discovery across
                  multiple domains.
                </p>
              </div>

              {/* Input Form Container */}
              <div className="bg-gradient-to-br from-white/5 to-white/2 border border-white/20 rounded-2xl p-6 space-y-4">
                {/* Main Prompt Input */}
                <div>
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Input text field for prompt"
                    disabled={isLoading}
                    className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-xl text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-teal-500 transition-colors"
                  />
                </div>

                {/* Number Input Fields */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-2 block">Number of Ideas</label>
                    <input
                      type="number"
                      value={numIdeas}
                      onChange={(e) => setNumIdeas(e.target.value)}
                      min="1"
                      max="20"
                      disabled={isLoading}
                      className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-foreground focus:outline-none focus:border-teal-500 transition-colors text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-2 block">Max Papers</label>
                    <input
                      type="number"
                      value={maxPapers}
                      onChange={(e) => setMaxPapers(e.target.value)}
                      min="1"
                      max="50"
                      disabled={isLoading}
                      className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-foreground focus:outline-none focus:border-teal-500 transition-colors text-sm"
                    />
                  </div>
                </div>

                {/* Submit Button */}
                <Button
                  onClick={handleSendMessage}
                  disabled={isLoading || !inputValue.trim()}
                  className="w-full bg-teal-600 text-white hover:bg-teal-700 disabled:opacity-50 py-3 font-medium"
                >
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  {isLoading ? "Generating..." : "Generate Research Ideas"}
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {message.role === "assistant" && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-cyan-600 flex items-center justify-center flex-shrink-0">
                    <span className="text-sm text-white font-bold">S</span>
                  </div>
                )}

                <div
                  className={`max-w-xs md:max-w-md lg:max-w-lg px-4 py-3 rounded-lg ${
                    message.role === "user"
                      ? "bg-teal-600/20 text-foreground rounded-br-none border border-teal-500/30"
                      : "bg-white/10 text-foreground border border-white/20 rounded-bl-none"
                  }`}
                >
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                  <span className="text-xs opacity-50 mt-1 block">
                    {message.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>

                {message.role === "user" && (
                  <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0 border border-white/20">
                    <span className="text-sm">👤</span>
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-cyan-600 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm text-white font-bold">S</span>
                </div>
                <div className="bg-white/10 border border-white/20 rounded-lg rounded-bl-none px-4 py-3">
                  <Loader2 className="h-4 w-4 animate-spin text-teal-500" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area - Only shown when there are messages */}
      {messages.length > 1 || (messages.length === 1 && messages[0].role === "user") ? (
        <div className="border-t border-white/10 p-4 md:p-6 bg-background">
          <form onSubmit={handleSendMessage} className="flex gap-3">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask about hypothesis generation, experiments, or research insights..."
              disabled={isLoading}
              className="bg-white/5 border border-white/10 text-foreground placeholder:text-muted-foreground focus:border-teal-500"
            />
            <Button
              type="submit"
              disabled={isLoading || !inputValue.trim()}
              className="bg-teal-600 text-white hover:bg-teal-700 px-4"
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      ) : null}
    </div>
  )
}
