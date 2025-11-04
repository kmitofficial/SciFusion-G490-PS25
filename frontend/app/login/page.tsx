"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card } from "@/components/ui/card"
import { useToast } from "@/hooks/use-toast"

export default function LoginPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        throw new Error("Login failed")
      }

      const data = await response.json()
      localStorage.setItem("auth_token", data.access_token)

      toast({ title: "Success", description: "Logged in successfully" })
      router.push("/app/dashboard")
    } catch (error) {
      toast({ title: "Error", description: "Invalid credentials", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center px-4">
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-600 rounded-full blur-3xl -z-10" />
      </div>

      <Card className="w-full max-w-md bg-white/5 border-white/10 backdrop-blur">
        <div className="p-8">
          <h1 className="text-2xl font-bold mb-6">Sign In</h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email" className="text-gray-300">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-2 bg-white/10 border-white/20 text-white placeholder:text-gray-500"
                required
              />
            </div>

            <div>
              <Label htmlFor="password" className="text-gray-300">
                Password
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-2 bg-white/10 border-white/20 text-white placeholder:text-gray-500"
                required
              />
            </div>

            <Button type="submit" disabled={loading} className="w-full bg-white text-black hover:bg-white/90">
              {loading ? "Signing In..." : "Sign In"}
            </Button>
          </form>

          <p className="text-gray-400 text-sm mt-4 text-center">
            Don't have an account?{" "}
            <button onClick={() => router.push("/signup")} className="text-white hover:underline font-semibold">
              Sign Up
            </button>
          </p>
        </div>
      </Card>
    </div>
  )
}
