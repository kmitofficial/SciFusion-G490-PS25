"use client"

export const dynamic = "force-dynamic"

import { Suspense, useCallback, useEffect, useRef, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"

import { ChatInterface, INITIAL_ASSISTANT_MESSAGE, type Message, type Thought } from "@/components/chat/chat-interface"
import { ChatSidebar, type SidebarChatItem } from "@/components/chat/chat-sidebar"
import { useAuth } from "@/hooks/use-auth"
import { apiFetch } from "@/lib/api-client"

interface ChatListItemResponse {
  chat_id: string
  title: string
  session_id: string
  project_slug: string
  created_at: string
}

interface ChatResponse extends ChatListItemResponse {}

interface ChatMessageResponse {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
  thoughts?: Thought[]
}

interface ChatMessagesResponse {
  messages: ChatMessageResponse[]
}

const createInitialMessage = (): Message => ({
  ...INITIAL_ASSISTANT_MESSAGE,
  id: crypto.randomUUID(),
  timestamp: new Date(),
})

const messageSignature = (message: Message): string =>
  JSON.stringify({
    role: message.role,
    content: message.content,
    timestamp: message.timestamp.toISOString(),
    thoughts: (message.thoughts ?? []).map((thought) => ({
      title: thought.title,
      detail: thought.detail,
    })),
  })

const messagesToRequestPayload = (messages: Message[]) =>
  messages.map((message) => ({
    id: message.id,
    role: message.role,
    content: message.content,
    timestamp: message.timestamp.toISOString(),
    thoughts: message.thoughts ?? [],
  }))

const responseToMessages = (responses: ChatMessageResponse[]): Message[] =>
  responses.map((item) => ({
    id: item.id,
    role: item.role,
    content: item.content,
    timestamp: new Date(item.timestamp),
    thoughts: item.thoughts ?? [],
  }))

function ChatPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const selectedChatId = searchParams.get("chatId")

  const { token, isAuthenticated, isLoading: authLoading } = useAuth()

  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [messagesByChat, setMessagesByChat] = useState<Record<string, Message[]>>({})
  const [draftMessages, setDraftMessages] = useState<Message[]>([createInitialMessage()])
  const [chats, setChats] = useState<SidebarChatItem[]>([])
  const [chatsLoading, setChatsLoading] = useState(false)
  const [activeChat, setActiveChat] = useState<ChatResponse | null>(null)
  const [isFetchingChat, setIsFetchingChat] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const persistedMessagesRef = useRef<Record<string, Record<string, string>>>({})
  const [deletingChatIds, setDeletingChatIds] = useState<string[]>([])

  const persistMessages = useCallback(
    async (chatId: string, messages: Message[]) => {
      if (!token || messages.length === 0) return

      try {
        setError(null)
        await apiFetch(
          `/chats/${chatId}/messages`,
          {
            method: "POST",
            body: JSON.stringify({ messages: messagesToRequestPayload(messages) }),
          },
          token,
        )

        const existing = persistedMessagesRef.current[chatId] ?? {}
        const next = { ...existing }
        for (const message of messages) {
          next[message.id] = messageSignature(message)
        }
        persistedMessagesRef.current[chatId] = next
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to save chat history")
      }
    },
    [token],
  )

  const loadChats = useCallback(async () => {
    if (!token) return
    setChatsLoading(true)
    try {
      setError(null)
      const response = await apiFetch<ChatListItemResponse[]>("/chats", {}, token)
      const sidebarItems = response.map((item) => ({
        chatId: item.chat_id,
        title: item.title,
        createdAt: item.created_at,
      }))
      setChats(sidebarItems)

      if (!selectedChatId && sidebarItems.length > 0) {
        router.replace(`/chat?chatId=${sidebarItems[0].chatId}`, { scroll: false })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load chats")
    } finally {
      setChatsLoading(false)
    }
  }, [router, selectedChatId, token])

  const loadChatDetail = useCallback(
    async (chatId: string) => {
      if (!token) return
      setIsFetchingChat(true)
      try {
        setError(null)
        const detail = await apiFetch<ChatResponse>(`/chats/${chatId}`, {}, token)
        setActiveChat(detail)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load chat details")
        setActiveChat(null)
      } finally {
        setIsFetchingChat(false)
      }
    },
    [token],
  )

  const loadChatMessages = useCallback(
    async (chatId: string) => {
      if (!token) return
      try {
        setError(null)
        const data = await apiFetch<ChatMessagesResponse>(`/chats/${chatId}/messages`, {}, token)
        const parsed = responseToMessages(data.messages)
        const nextMessages = parsed.length > 0 ? parsed : [createInitialMessage()]
        setMessagesByChat((prev) => ({
          ...prev,
          [chatId]: nextMessages.map((message) => ({ ...message })),
        }))

        const signatures: Record<string, string> = {}
        for (const message of parsed) {
          signatures[message.id] = messageSignature(message)
        }
        persistedMessagesRef.current[chatId] = signatures
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load chat messages")
        setMessagesByChat((prev) => ({
          ...prev,
          [chatId]: [createInitialMessage()],
        }))
        persistedMessagesRef.current[chatId] = {}
      }
    },
    [token],
  )

  useEffect(() => {
    if (token) {
      loadChats()
    }
  }, [token, loadChats])

  useEffect(() => {
    if (!token || !selectedChatId) return
    if (persistedMessagesRef.current[selectedChatId] !== undefined) return
    void loadChatMessages(selectedChatId)
  }, [token, selectedChatId, loadChatMessages])

  useEffect(() => {
    if (token && selectedChatId) {
      loadChatDetail(selectedChatId)
    } else {
      setActiveChat(null)
    }
  }, [token, selectedChatId, loadChatDetail])

  const handleSelectChat = (chatId: string) => {
    router.replace(`/chat?chatId=${chatId}`, { scroll: false })
  }

  const handleNewChat = () => {
    router.replace(`/chat`, { scroll: false })
    setActiveChat(null)
    setDraftMessages([createInitialMessage()])
  }

  const handleDeleteChat = useCallback(
    async (chatId: string) => {
      if (!token || deletingChatIds.includes(chatId)) return

      setDeletingChatIds((prev) => [...prev, chatId])
      try {
        setError(null)
        await apiFetch(`/chats/${chatId}`, { method: "DELETE" }, token)

        let nextSelected: string | null = null
        setChats((prev) => {
          const filtered = prev.filter((item) => item.chatId !== chatId)
          nextSelected = filtered[0]?.chatId ?? null
          return filtered
        })

        setMessagesByChat((prev) => {
          const { [chatId]: _removed, ...rest } = prev
          return rest
        })
        delete persistedMessagesRef.current[chatId]

        if (selectedChatId === chatId) {
          setActiveChat(null)
          if (nextSelected) {
            router.replace(`/chat?chatId=${nextSelected}`, { scroll: false })
          } else {
            router.replace(`/chat`, { scroll: false })
            setDraftMessages([createInitialMessage()])
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to delete chat")
      } finally {
        setDeletingChatIds((prev) => prev.filter((id) => id !== chatId))
      }
    },
    [token, deletingChatIds, selectedChatId, router],
  )

  const handleToggleSidebar = useCallback(() => {
    setIsSidebarOpen((previous) => {
      const next = !previous
      if (next) {
        setIsSidebarCollapsed(false)
      }
      return next
    })
  }, [])

  const handleChatCreated = (chat: ChatResponse) => {
    setActiveChat(chat)
    const seedMessages = (draftMessages.length > 0 ? draftMessages : [createInitialMessage()]).map((message) => ({
      ...message,
    }))

    setMessagesByChat((prev) => ({
      ...prev,
      [chat.chat_id]: seedMessages,
    }))
    persistedMessagesRef.current[chat.chat_id] = {}
    void persistMessages(chat.chat_id, seedMessages)
    setDraftMessages([createInitialMessage()])
    setChats((prev) => {
      const filtered = prev.filter((item) => item.chatId !== chat.chat_id)
      return [
        { chatId: chat.chat_id, title: chat.title, createdAt: chat.created_at },
        ...filtered,
      ]
    })
    router.replace(`/chat?chatId=${chat.chat_id}`, { scroll: false })
  }

  const handleMessagesUpdate = useCallback(
    (chatIdentifier: string | null, updated: Message[]) => {
      if (chatIdentifier) {
        const nextMessages = updated.map((message) => ({ ...message }))
        setMessagesByChat((prev) => ({
          ...prev,
          [chatIdentifier]: nextMessages,
        }))

        const signatures = persistedMessagesRef.current[chatIdentifier] ?? {}
        const toPersist = nextMessages.filter((message) => signatures[message.id] !== messageSignature(message))
        if (toPersist.length > 0) {
          void persistMessages(chatIdentifier, toPersist)
        }
      } else {
        setDraftMessages(updated.map((message) => ({ ...message })))
      }
    },
    [persistMessages],
  )

  const sessionId = activeChat?.session_id ?? null
  const activeMessages = selectedChatId
    ? messagesByChat[selectedChatId] ?? [createInitialMessage()]
    : draftMessages

  if (!authLoading && !isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center bg-background text-foreground">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-semibold">Sign in required</h1>
          <p className="text-muted-foreground">Please log in to access your research chats.</p>
          <button
            onClick={() => router.push("/login")}
            className="rounded bg-primary px-4 py-2 font-medium text-primary-foreground"
          >
            Go to login
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {isSidebarOpen && (
        <div className="fixed inset-0 bg-black/50 md:hidden z-30" onClick={() => setIsSidebarOpen(false)} />
      )}

      <ChatSidebar
        chats={chats}
        selectedId={selectedChatId}
        onSelectConversation={handleSelectChat}
        onCreateConversation={handleNewChat}
        onDeleteConversation={handleDeleteChat}
        isMobileOpen={isSidebarOpen}
        onCloseMobile={() => setIsSidebarOpen(false)}
        isLoading={chatsLoading}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapsed={() => setIsSidebarCollapsed((prev) => !prev)}
        deletingIds={deletingChatIds}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        {error && (
          <div className="border-b border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        )}

        <ChatInterface
          chatId={selectedChatId}
          sessionId={sessionId}
          token={token ?? null}
          onChatCreated={handleChatCreated}
          onToggleSidebar={handleToggleSidebar}
          initialMessages={activeMessages}
          onMessagesUpdate={handleMessagesUpdate}
        />

        {isFetchingChat && selectedChatId && (
          <div className="absolute bottom-4 right-4 rounded bg-white/10 px-3 py-2 text-xs text-muted-foreground">
            Loading chat data…
          </div>
        )}
      </div>
    </div>
  )
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center">Loading chat…</div>}>
      <ChatPageContent />
    </Suspense>
  )
}
