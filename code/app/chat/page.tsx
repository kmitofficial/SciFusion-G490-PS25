"use client"

import { useState } from "react"
import { ChatInterface } from "@/components/chat/chat-interface"
import { ChatSidebar } from "@/components/chat/chat-sidebar"
import { Button } from "@/components/ui/button"
import { Menu, X } from "lucide-react"

export default function DashboardPage() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null)

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && (
        <div className="fixed inset-0 bg-black/50 md:hidden z-30" onClick={() => setIsSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <ChatSidebar
        selectedId={selectedConversation}
        onSelectConversation={setSelectedConversation}
        isMobileOpen={isSidebarOpen}
        onCloseMobile={() => setIsSidebarOpen(false)}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <div className="flex items-center justify-between h-16 px-4 md:px-6 border-b border-white/10 bg-background">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="md:hidden text-foreground"
          >
            {isSidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
          <h1 className="text-lg font-semibold text-foreground">Scifusion</h1>
          <div className="w-10" />
        </div>

        {/* Chat Content */}
        <ChatInterface conversationId={selectedConversation} />
      </div>
    </div>
  )
}
