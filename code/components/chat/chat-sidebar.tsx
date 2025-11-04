"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Plus, Trash2, LogOut, Settings, Search, Library, Compass, User, ChevronUp } from "lucide-react"

interface Conversation {
  id: string
  title: string
  date: string
}

interface ChatSidebarProps {
  selectedId: string | null
  onSelectConversation: (id: string) => void
  isMobileOpen: boolean
  onCloseMobile: () => void
}

export function ChatSidebar({ selectedId, onSelectConversation, isMobileOpen, onCloseMobile }: ChatSidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([
    { id: "1", title: "Hypothesis generation in drug discovery", date: "Today" },
    { id: "2", title: "Materials science validation", date: "Yesterday" },
    { id: "3", title: "Environmental modeling approach", date: "2 days ago" },
    { id: "4", title: "Multi-agent research framework", date: "1 week ago" },
  ])
  const [isProfileOpen, setIsProfileOpen] = useState(false)

  const handleNewConversation = () => {
    const newId = String(Math.max(...conversations.map((c) => Number.parseInt(c.id)), 0) + 1)
    const newConversation = {
      id: newId,
      title: "New research session",
      date: "Today",
    }
    setConversations([newConversation, ...conversations])
    onSelectConversation(newId)
    onCloseMobile()
  }

  const handleDeleteConversation = (id: string) => {
    setConversations(conversations.filter((c) => c.id !== id))
    if (selectedId === id) {
      onSelectConversation(conversations[0]?.id || "")
    }
  }

  return (
    <>
      {/* Sidebar */}
      <div
        className={`fixed md:relative md:flex flex-col w-64 h-screen bg-gradient-to-b from-white/5 to-transparent border-r border-white/10 transition-all duration-300 z-40 ${
          isMobileOpen ? "left-0" : "-left-64"
        }`}
      >
        {/* Top Actions */}
        <div className="p-4 space-y-3 border-b border-white/10">
          {/* Scifusion Header */}
          <Link href="/" className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-500 to-cyan-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">S</span>
            </div>
            <span className="font-semibold text-foreground">Scifusion</span>
          </Link>

          {/* New Chat Button */}
          <Button
            onClick={handleNewConversation}
            className="w-full bg-white/10 text-foreground hover:bg-white/20 border border-white/20 rounded-lg font-medium justify-start"
          >
            <Plus className="h-4 w-4 mr-2" />
            New chat
          </Button>
        </div>

        {/* Quick Actions */}
        <div className="px-3 py-3 space-y-2 border-b border-white/10">
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors text-sm">
            <Search className="h-4 w-4" />
            Search chats
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors text-sm">
            <Library className="h-4 w-4" />
            Library
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors text-sm">
            <Compass className="h-4 w-4" />
            Explore
          </button>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto px-3 py-4">
          <p className="text-xs font-semibold text-muted-foreground px-2 mb-3">Recent</p>
          <div className="space-y-2">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                onClick={() => {
                  onSelectConversation(conversation.id)
                  onCloseMobile()
                }}
                className="group relative"
              >
                <button
                  className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                    selectedId === conversation.id
                      ? "bg-white/10 text-foreground"
                      : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                  }`}
                >
                  <p className="text-sm font-medium truncate">{conversation.title}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{conversation.date}</p>
                </button>

                {/* Delete Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDeleteConversation(conversation.id)
                  }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Trash2 className="h-4 w-4 text-muted-foreground hover:text-red-400" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Footer with Profile */}
        <div className="border-t border-white/10 p-3 space-y-2">
          <Button
            variant="ghost"
            className="w-full justify-start text-muted-foreground hover:text-foreground hover:bg-white/5 text-sm"
          >
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>

          <div className="relative">
            <button
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors text-sm"
            >
              <div className="flex items-center gap-2">
                <User className="h-4 w-4" />
                <span>Profile</span>
              </div>
              <ChevronUp className={`h-4 w-4 transition-transform ${isProfileOpen ? "rotate-180" : ""}`} />
            </button>

            {/* Profile Dropdown */}
            {isProfileOpen && (
              <div className="absolute bottom-full left-0 right-0 mb-2 rounded-lg bg-white/10 border border-white/20 overflow-hidden">
                <Link href="/" onClick={() => setIsProfileOpen(false)} className="block w-full">
                  <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors text-left">
                    <LogOut className="h-4 w-4" />
                    Logout
                  </button>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
