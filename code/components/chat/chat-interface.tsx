"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
} from "@/components/ui/drawer"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"
import {
  Brain,
  Loader2,
  Menu,
  PanelRightClose,
  PanelRightOpen,
  Settings2,
  Sparkles,
  User,
} from "lucide-react"

import { useSessionEvents } from "@/hooks/use-session-events"
import { apiFetch } from "@/lib/api-client"

const SYSTEM_PROMPT =
  "You are SciFusion's research copilot. Provide concise, evidence-driven insights and suggest next experimental steps when possible."

export interface Thought {
  title: string
  detail: string
}

interface ChatSummary {
  chat_id: string
  session_id: string
  project_slug: string
  title: string
  created_at: string
}

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  thoughts?: Thought[]
}

interface ChatInterfaceProps {
  chatId: string | null
  sessionId: string | null
  token: string | null
  onChatCreated: (chat: ChatSummary) => void
  onToggleSidebar: () => void
  initialMessages?: Message[]
  onMessagesUpdate: (chatId: string | null, messages: Message[]) => void
}

const stageOrder = [
  "QUEUED",
  "PREPARING",
  "RETRIEVAL",
  "IDEA_GENERATION",
  "NOVELTY_CHECK",
  "EXECUTION",
  "COMPLETE",
  "FAILED",
]

const stageLabels: Record<string, string> = {
  QUEUED: "Queued",
  PREPARING: "Preparing",
  RETRIEVAL: "Retrieval",
  IDEA_GENERATION: "Idea generation",
  NOVELTY_CHECK: "Novelty check",
  EXECUTION: "Experiment execution",
  COMPLETE: "Complete",
  FAILED: "Failed",
}

export const INITIAL_ASSISTANT_MESSAGE: Message = {
  id: "intro",
  role: "assistant",
  content:
    "Welcome to SciFusion. Share the research problem you're exploring, and I'll help orchestrate project setup, literature review, hypothesis generation, and automated experimentation.",
  timestamp: new Date(),
}

export function ChatInterface({
  chatId,
  sessionId,
  token,
  onChatCreated,
  onToggleSidebar,
  initialMessages = [INITIAL_ASSISTANT_MESSAGE],
  onMessagesUpdate,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>(() => initialMessages.map((message) => ({ ...message })))
  const [inputValue, setInputValue] = useState("")
  const [numIdeas, setNumIdeas] = useState("5")
  const [maxPapers, setMaxPapers] = useState("10")
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isInspectorOpen, setIsInspectorOpen] = useState(true)
  const [isMobileInspectorOpen, setIsMobileInspectorOpen] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatIdRef = useRef<string | null>(chatId)
  const { events, groupedByStage, state: streamState } = useSessionEvents(sessionId)

  useEffect(() => {
    chatIdRef.current = chatId
  }, [chatId])

  useEffect(() => {
    setMessages(initialMessages.map((message) => ({ ...message })))
  }, [chatId, initialMessages])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const orderedStages = useMemo(() => {
    return stageOrder
      .map((stage) => ({ stage, events: groupedByStage[stage] ?? [] }))
      .filter((entry) => entry.events.length > 0)
  }, [groupedByStage])

  const handleSendMessage = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!inputValue.trim()) return

    const parsedIdeas = Number.parseInt(numIdeas, 10)
    const parsedPapers = Number.parseInt(maxPapers, 10)

    if (Number.isNaN(parsedIdeas) || parsedIdeas <= 0) {
      setErrorMessage("Number of ideas must be a positive number")
      return
    }

    if (Number.isNaN(parsedPapers) || parsedPapers < 0) {
      setErrorMessage("Max papers must be zero or greater")
      return
    }

    if (!token) {
      setErrorMessage("You must be signed in to chat with the assistant.")
      return
    }

    setErrorMessage(null)

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    }

    const nextMessages = [...messages, userMessage]
    setMessages(nextMessages)
    setInputValue("")
    setIsLoading(true)
    onMessagesUpdate(chatIdRef.current, nextMessages)

    try {
      if (!chatId) {
        const created = await apiFetch<ChatSummary>(
          "/chats",
          {
            method: "POST",
            body: JSON.stringify({
              prompt: userMessage.content,
              num_ideas: parsedIdeas,
              max_papers: parsedPapers,
            }),
          },
          token,
        )

        chatIdRef.current = created.chat_id
        onChatCreated(created)
      }

      const payloadMessages = nextMessages.map((message) => ({
        role: message.role,
        content: message.content,
      }))

      const response = await apiFetch<{
        content: string
        thoughts?: Thought[]
      }>(
        "/ai/chat",
        {
          method: "POST",
          body: JSON.stringify({
            model: "gemini-2.5-flash-lite",
            system_prompt: SYSTEM_PROMPT,
            messages: payloadMessages,
          }),
        },
        token,
      )

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.content,
        thoughts: response.thoughts ?? [],
        timestamp: new Date(),
      }

      setMessages((prev) => {
        const updated = [...prev, assistantMessage]
        onMessagesUpdate(chatIdRef.current, updated)
        return updated
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to get AI response"
      setErrorMessage(message)
      setMessages((prev) => {
        const fallback: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `Sorry, I ran into a problem: ${message}`,
          timestamp: new Date(),
        }
        const updated = [...prev, fallback]
        onMessagesUpdate(chatIdRef.current, updated)
        return updated
      })
    } finally {
      setIsLoading(false)
    }
  }

  const insightsPanel = (
    <div className="flex h-full flex-col">
      <div className="border-b border-border/60 px-5 py-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">AutoAD pipeline</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Live reasoning trace from the backend execution. Expand a stage to inspect individual events.
        </p>
      </div>
      <ScrollArea className="flex-1 px-4">
        <div className="space-y-6 py-4">
          {orderedStages.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              {streamState === "connecting"
                ? "Connecting to session stream..."
                : "No events yet. Kick off a chat to see the pipeline unfold."}
            </div>
          ) : (
            orderedStages.map(({ stage, events }) => (
              <Card key={stage} className="border border-border/40 bg-background/60">
                <div className="flex items-center justify-between border-b border-border/60 px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="bg-teal-500/10 text-teal-300">
                      {stageLabels[stage] ?? stage}
                    </Badge>
                    <span className="text-xs text-muted-foreground">{events.length} update{events.length === 1 ? "" : "s"}</span>
                  </div>
                  <span className="text-xs text-muted-foreground uppercase tracking-wide">{events[0]?.timestamp ? new Date(events[0].timestamp).toLocaleTimeString() : ""}</span>
                </div>
                <div className="space-y-3 px-4 py-3 text-sm">
                  {events.map((event, index) => (
                    <div key={`${stage}-${index}`} className="space-y-1">
                      <p className="font-medium text-foreground">{event.message}</p>
                      {event.metadata && Object.keys(event.metadata).length > 0 ? (
                        <pre className="whitespace-pre-wrap rounded-md bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
                          {JSON.stringify(event.metadata, null, 2)}
                        </pre>
                      ) : null}
                    </div>
                  ))}
                </div>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>
      <div className="border-t border-border/60 px-4 py-3 text-xs text-muted-foreground">
        Stream status: <span className="font-medium text-foreground">{streamState}</span>
      </div>
    </div>
  )

  return (
    <div className="relative flex h-full w-full overflow-hidden rounded-3xl border border-border/30 bg-gradient-to-br from-slate-900/70 via-slate-900/40 to-slate-950/60 shadow-xl backdrop-blur">
      <Drawer open={isMobileInspectorOpen} onOpenChange={setIsMobileInspectorOpen}>
        <DrawerContent className="h-[85vh]">
          <DrawerHeader>
            <DrawerTitle className="flex items-center gap-2 text-base">
              <Brain className="h-4 w-4 text-teal-300" /> Live reasoning
            </DrawerTitle>
            <DrawerDescription>Realtime progress from the AutoAD execution pipeline.</DrawerDescription>
          </DrawerHeader>
          <div className="flex-1 overflow-hidden px-2 pb-2">
            {insightsPanel}
          </div>
          <DrawerFooter>
            <DrawerClose asChild>
              <Button variant="secondary">Close</Button>
            </DrawerClose>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>

      <div className="flex flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-border/60 px-4 lg:px-6">
          <div className="flex items-center gap-3">
            <button
              onClick={onToggleSidebar}
              className="flex h-10 w-10 items-center justify-center rounded-lg border border-border/40 text-muted-foreground transition hover:bg-white/5 lg:hidden"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-teal-500/30 to-cyan-500/40 text-white">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">SciFusion Copilot</p>
                <p className="text-xs text-muted-foreground">Research orchestration workspace</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              className="hidden md:flex items-center gap-2"
              onClick={() => setIsInspectorOpen((prev) => !prev)}
            >
              {isInspectorOpen ? <PanelRightClose className="h-4 w-4" /> : <PanelRightOpen className="h-4 w-4" />}
              {isInspectorOpen ? "Hide pipeline" : "Show pipeline"}
            </Button>
            <Button
              variant="secondary"
              className="md:hidden"
              onClick={() => setIsMobileInspectorOpen(true)}
            >
              <Brain className="h-4 w-4" />
            </Button>
            <Button variant="outline" className="h-10 w-10 rounded-lg border-border/40 text-muted-foreground">
              <Settings2 className="h-4 w-4" />
            </Button>
          </div>
        </header>

        <main className="flex-1 overflow-hidden">
          <div className="flex h-full flex-col">
            <ScrollArea className="flex-1 px-4 py-6 lg:px-8">
              <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
                {errorMessage ? (
                  <Alert variant="destructive">
                    <AlertDescription>{errorMessage}</AlertDescription>
                  </Alert>
                ) : null}

                {messages.map((message) => {
                  const isAssistant = message.role === "assistant"
                  return (
                    <div key={message.id} className={cn("flex w-full", isAssistant ? "justify-start" : "justify-end")}
                    >
                      <div
                        className={cn(
                          "relative max-w-full rounded-2xl border px-5 py-4 text-sm shadow-lg", 
                          isAssistant
                            ? "border-teal-500/30 bg-gradient-to-br from-teal-500/10 via-slate-900/60 to-cyan-500/10 text-foreground"
                            : "border-teal-500/40 bg-gradient-to-br from-teal-600/80 to-emerald-600/80 text-white",
                        )}
                      >
                        <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground/80">
                          {isAssistant ? (
                            <span className="flex items-center gap-1 text-teal-200">
                              <Sparkles className="h-3 w-3" /> Assistant
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-white/80">
                              <User className="h-3 w-3" /> You
                            </span>
                          )}
                          <span className="text-muted-foreground/60">
                            {message.timestamp.toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                        </div>
                        <Separator className="my-3 opacity-20" />
                        <div className="space-y-3 text-sm leading-relaxed">
                          <p className="whitespace-pre-wrap">{message.content}</p>
                          {isAssistant && message.thoughts && message.thoughts.length > 0 ? (
                            <Accordion type="single" collapsible className="rounded-xl border border-teal-500/20 bg-black/30">
                              <AccordionItem value="thoughts">
                                <AccordionTrigger className="px-4 text-xs font-semibold uppercase tracking-wide text-teal-200">
                                  View reasoning trail
                                </AccordionTrigger>
                                <AccordionContent className="space-y-3 px-4">
                                  {message.thoughts.map((thought, index) => (
                                    <div key={`${message.id}-thought-${index}`} className="rounded-lg border border-white/10 bg-white/5 p-3">
                                      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                                        {thought.title}
                                      </p>
                                      <p className="mt-1 text-sm text-foreground/90 whitespace-pre-wrap">
                                        {thought.detail}
                                      </p>
                                    </div>
                                  ))}
                                </AccordionContent>
                              </AccordionItem>
                            </Accordion>
                          ) : null}
                        </div>
                      </div>
                    </div>
                  )
                })}

                {isLoading ? (
                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin text-teal-200" /> Generating response…
                  </div>
                ) : null}

                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            <div className="border-t border-border/60 bg-background/60 px-4 py-4 lg:px-8">
              <form onSubmit={handleSendMessage} className="mx-auto flex w-full max-w-3xl flex-col gap-3">
                <div className="flex flex-col gap-3 md:flex-row">
                  <Input
                    value={inputValue}
                    onChange={(event) => setInputValue(event.target.value)}
                    placeholder="Describe the research question or dataset you'd like to explore."
                    disabled={isLoading}
                    className="flex-1 border border-border/40 bg-black/40 text-sm text-foreground placeholder:text-muted-foreground"
                  />
                  <Button
                    type="submit"
                    disabled={isLoading || !inputValue.trim()}
                    className="h-11 gap-2 bg-teal-600 text-sm font-semibold text-white hover:bg-teal-500"
                  >
                    {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                    {isLoading ? "Generating" : "Ask the copilot"}
                  </Button>
                </div>

                <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <label className="font-medium">Ideas</label>
                    <Input
                      type="number"
                      min={1}
                      max={20}
                      value={numIdeas}
                      onChange={(event) => setNumIdeas(event.target.value)}
                      disabled={isLoading || !!chatId}
                      className="h-9 w-20 border border-border/40 bg-black/40"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="font-medium">Max papers</label>
                    <Input
                      type="number"
                      min={0}
                      max={50}
                      value={maxPapers}
                      onChange={(event) => setMaxPapers(event.target.value)}
                      disabled={isLoading || !!chatId}
                      className="h-9 w-24 border border-border/40 bg-black/40"
                    />
                  </div>
                  <span className="hidden md:inline text-muted-foreground">Session ID: {sessionId ?? "new"}</span>
                </div>
              </form>
            </div>
          </div>
        </main>
      </div>

      <aside
        className={cn(
          "hidden w-[360px] flex-col border-l border-border/40 bg-black/40 xl:flex",
          isInspectorOpen ? "xl:flex" : "xl:hidden",
        )}
      >
        {insightsPanel}
      </aside>
    </div>
  )
}
