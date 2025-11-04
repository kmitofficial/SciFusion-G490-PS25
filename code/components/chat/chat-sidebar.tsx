"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import {
  Plus,
  LogOut,
  Settings,
  Search,
  Library,
  Compass,
  User,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  Trash2,
  Loader2,
} from "lucide-react"

export interface SidebarChatItem {
  chatId: string
  title: string
  createdAt: string
}

interface ChatSidebarProps {
  chats: SidebarChatItem[]
  selectedId: string | null
  onSelectConversation: (id: string) => void
  onCreateConversation: () => void
  onDeleteConversation: (id: string) => void | Promise<void>
  isMobileOpen: boolean
  onCloseMobile: () => void
  isLoading?: boolean
  isCollapsed: boolean
  onToggleCollapsed: () => void
  deletingIds?: string[]
}

export function ChatSidebar({
  chats,
  selectedId,
  onSelectConversation,
  onCreateConversation,
  onDeleteConversation,
  isMobileOpen,
  onCloseMobile,
  isLoading = false,
  isCollapsed,
  onToggleCollapsed,
  deletingIds = [],
}: ChatSidebarProps) {
  const [isProfileOpen, setIsProfileOpen] = useState(false)

  const buildInitials = (title: string) => {
    const initials = title
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((word) => word[0]?.toUpperCase() ?? "")
      .join("")
    return initials || "AI"
  }

  return (
    <>
      {/* Sidebar */}
      <div
        data-collapsed={isCollapsed}
        className={cn(
          "group/sidebar fixed flex h-screen w-64 flex-col border-r border-white/10 bg-gradient-to-b from-white/5 to-transparent transition-[left,width] duration-300 z-40",
          isMobileOpen ? "left-0" : "-left-64",
          isCollapsed ? "md:w-20" : "md:w-72",
          "md:relative md:left-0",
        )}
      >
        {/* Top Actions */}
        <div className="border-b border-white/10 p-4">
          <div className="flex items-center justify-between gap-2">
            {/* Scifusion Header */}
            <Link
              href="/"
              className={cn(
                "flex h-10 flex-1 items-center gap-2",
                "group-data-[collapsed=true]/sidebar:justify-center",
              )}
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-teal-500 to-cyan-600">
                <span className="text-sm font-bold text-white">S</span>
              </div>
              <span className="font-semibold text-foreground group-data-[collapsed=true]/sidebar:hidden">
                Scifusion
              </span>
            </Link>
            <button
              type="button"
              onClick={() => {
                onToggleCollapsed()
                if (isProfileOpen) setIsProfileOpen(false)
              }}
              className="hidden h-9 w-9 items-center justify-center rounded-lg border border-white/10 text-muted-foreground transition hover:bg-white/10 hover:text-foreground md:flex"
              aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
            </button>
          </div>

          {/* New Chat Button */}
          <Button
            onClick={() => {
              onCreateConversation()
              onCloseMobile()
            }}
            className={cn(
              "mt-3 w-full justify-start rounded-lg border border-white/20 bg-white/10 font-medium text-foreground hover:bg-white/20",
              "group-data-[collapsed=true]/sidebar:justify-center group-data-[collapsed=true]/sidebar:px-2",
            )}
          >
            <Plus className="mr-2 h-4 w-4 group-data-[collapsed=true]/sidebar:mr-0" />
            <span className="group-data-[collapsed=true]/sidebar:hidden">New chat</span>
          </Button>
        </div>

        {/* Quick Actions */}
        <div className="space-y-2 border-b border-white/10 px-3 py-3">
          <button
            className={cn(
              "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-white/5 hover:text-foreground",
              "group-data-[collapsed=true]/sidebar:justify-center group-data-[collapsed=true]/sidebar:gap-0",
            )}
          >
            <Search className="h-4 w-4" />
            <span className="group-data-[collapsed=true]/sidebar:hidden">Search chats</span>
          </button>
          <button
            className={cn(
              "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-white/5 hover:text-foreground",
              "group-data-[collapsed=true]/sidebar:justify-center group-data-[collapsed=true]/sidebar:gap-0",
            )}
          >
            <Library className="h-4 w-4" />
            <span className="group-data-[collapsed=true]/sidebar:hidden">Library</span>
          </button>
          <button
            className={cn(
              "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-white/5 hover:text-foreground",
              "group-data-[collapsed=true]/sidebar:justify-center group-data-[collapsed=true]/sidebar:gap-0",
            )}
          >
            <Compass className="h-4 w-4" />
            <span className="group-data-[collapsed=true]/sidebar:hidden">Explore</span>
          </button>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto px-3 py-4">
          <p className="mb-3 px-2 text-xs font-semibold text-muted-foreground group-data-[collapsed=true]/sidebar:text-center group-data-[collapsed=true]/sidebar:px-0">
            Recent
          </p>
          <div className="space-y-2">
            {isLoading ? (
              <p className="px-3 py-2 text-xs text-muted-foreground">Loading chats…</p>
            ) : chats.length === 0 ? (
              <p className="px-3 py-2 text-xs text-muted-foreground">No chats yet. Start a new one!</p>
            ) : (
              chats.map((chat) => {
                const isDeleting = deletingIds.includes(chat.chatId)
                return (
                  <div
                    key={chat.chatId}
                    onClick={() => {
                      onSelectConversation(chat.chatId)
                      onCloseMobile()
                    }}
                    className="group relative"
                  >
                    <button
                      className={cn(
                        "w-full rounded-lg px-3 py-2 text-left transition-colors",
                        selectedId === chat.chatId
                          ? "bg-white/10 text-foreground"
                          : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
                      )}
                    >
                      <div className="flex items-center gap-3 group-data-[collapsed=true]/sidebar:justify-center group-data-[collapsed=true]/sidebar:gap-0">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/5 text-xs font-semibold text-foreground">
                          {buildInitials(chat.title)}
                        </div>
                        <div className="min-w-0 group-data-[collapsed=true]/sidebar:hidden">
                          <p className="truncate text-sm font-medium">{chat.title}</p>
                          <p className="mt-0.5 text-xs text-muted-foreground">
                            {new Date(chat.createdAt).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </button>
                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation()
                        onDeleteConversation(chat.chatId)
                      }}
                      disabled={isDeleting}
                      className={cn(
                        "absolute right-2 top-1/2 hidden -translate-y-1/2 items-center justify-center rounded-md border border-white/20 bg-black/60 p-1 text-muted-foreground transition hover:text-foreground",
                        "group-hover:flex",
                        "group-data-[collapsed=true]/sidebar:hidden",
                        isDeleting ? "opacity-70" : "",
                      )}
                      aria-label="Delete chat"
                    >
                      {isDeleting ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
                    </button>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* Footer with Profile */}
        <div className="space-y-2 p-3">
          <div className="relative">
            <button
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              className={cn(
                "flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-white/5 hover:text-foreground",
                "group-data-[collapsed=true]/sidebar:justify-center group-data-[collapsed=true]/sidebar:px-2",
              )}
            >
              <div className="flex items-center gap-2">
                <User className="h-4 w-4" />
                <span className="group-data-[collapsed=true]/sidebar:hidden">Profile</span>
              </div>
              <ChevronUp
                className={cn(
                  "h-4 w-4 transition-transform group-data-[collapsed=true]/sidebar:hidden",
                  isProfileOpen ? "rotate-180" : "",
                )}
              />
            </button>

            {/* Profile Dropdown */}
            {isProfileOpen && !isCollapsed && (
              <div className="absolute bottom-full left-0 right-0 mb-2 overflow-hidden rounded-lg border border-white/20 bg-white/10">
                <Link href="/" onClick={() => setIsProfileOpen(false)} className="block w-full">
                  <button className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-muted-foreground transition-colors hover:bg-white/5 hover:text-foreground">
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
