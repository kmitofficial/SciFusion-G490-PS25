"use client"

import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth"
import { Button } from "@/components/ui/button"
import { useEffect } from "react"

export default function Home() {
  const router = useRouter()
  const { token, loading } = useAuth()

  useEffect(() => {
    if (!loading && token) {
      router.push("/app/dashboard")
    }
  }, [token, loading, router])

  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      {/* Animated background */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-600 rounded-full blur-3xl -z-10" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-indigo-600 rounded-full blur-3xl -z-10" />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 px-6 py-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">SciFusion</h1>
        <div className="space-x-4">
          <Button
            variant="ghost"
            onClick={() => router.push("/login")}
            className="text-white hover:text-white hover:bg-white/10"
          >
            Sign In
          </Button>
          <Button onClick={() => router.push("/signup")} className="bg-white text-black hover:bg-white/90">
            Sign Up
          </Button>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative z-10 max-w-6xl mx-auto px-6 py-20 text-center">
        <h2 className="text-6xl md:text-7xl font-bold mb-6 leading-tight">AI-Powered Research Automation</h2>
        <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
          Discover new scientific ideas and papers in real-time. Let AI augment your research process with our
          cutting-edge automation platform.
        </p>
        <div className="flex gap-4 justify-center">
          <Button
            onClick={() => router.push("/signup")}
            size="lg"
            className="bg-white text-black hover:bg-white/90 px-8"
          >
            Get Started
          </Button>
          <Button variant="outline" size="lg" className="border-white text-white hover:bg-white/10 px-8 bg-transparent">
            Learn More
          </Button>
        </div>
      </div>

      {/* Features */}
      <div className="relative z-10 max-w-6xl mx-auto px-6 py-20 grid md:grid-cols-3 gap-8">
        <div className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-2">Real-time Monitoring</h3>
          <p className="text-gray-400">Watch your experiments unfold with live logs and instant results</p>
        </div>
        <div className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-2">Smart Configuration</h3>
          <p className="text-gray-400">Configure experiments with AI model selection and advanced options</p>
        </div>
        <div className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-2">Research Insights</h3>
          <p className="text-gray-400">Get curated papers, ideas, and experimental results at your fingertips</p>
        </div>
      </div>
    </div>
  )
}
