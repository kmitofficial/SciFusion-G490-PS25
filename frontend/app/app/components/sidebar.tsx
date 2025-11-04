"use client"

import { useRouter, usePathname } from "next/navigation"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Plus, LogOut, Home } from "lucide-react"

interface Job {
  id: string
  topic: string
  status: string
  created_at: string
}

export default function Sidebar() {
  const router = useRouter()
  const pathname = usePathname()
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    try {
      const token = localStorage.getItem("auth_token")
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/jobs`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        const data = await response.json()
        setJobs(data)
      }
    } catch (error) {
      console.error("Failed to fetch jobs:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem("auth_token")
    router.push("/login")
  }

  return (
    <aside className="fixed left-0 top-0 w-64 h-screen bg-white/5 border-r border-white/10 backdrop-blur p-6 flex flex-col">
      {/* Logo */}
      <h1 className="text-xl font-bold mb-8">SciFusion</h1>

      {/* New Experiment Button */}
      <Button
        onClick={() => router.push("/app/dashboard")}
        className="w-full bg-white text-black hover:bg-white/90 mb-6"
      >
        <Plus className="w-4 h-4 mr-2" />
        New Experiment
      </Button>

      {/* Dashboard Link */}
      <Button
        variant={pathname === "/app/dashboard" ? "default" : "ghost"}
        onClick={() => router.push("/app/dashboard")}
        className="w-full justify-start text-left mb-6"
      >
        <Home className="w-4 h-4 mr-2" />
        Dashboard
      </Button>

      {/* Jobs List */}
      <div className="flex-1 overflow-y-auto mb-6">
        <p className="text-xs text-gray-400 uppercase tracking-widest mb-3">Recent Experiments</p>
        <div className="space-y-2">
          {loading ? (
            <p className="text-sm text-gray-400">Loading...</p>
          ) : jobs.length === 0 ? (
            <p className="text-sm text-gray-400">No experiments yet</p>
          ) : (
            jobs.slice(0, 10).map((job) => (
              <button
                key={job.id}
                onClick={() => router.push(`/app/experiment/${job.id}`)}
                className={`w-full text-left px-3 py-2 rounded text-sm transition ${
                  pathname === `/app/experiment/${job.id}` ? "bg-white/10 text-white" : "text-gray-300 hover:bg-white/5"
                }`}
              >
                <div className="truncate font-medium">{job.topic}</div>
                <div className="text-xs text-gray-500">{job.status}</div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Logout Button */}
      <Button
        variant="ghost"
        onClick={handleLogout}
        className="w-full justify-start text-red-400 hover:text-red-300 hover:bg-red-500/10"
      >
        <LogOut className="w-4 h-4 mr-2" />
        Logout
      </Button>
    </aside>
  )
}
