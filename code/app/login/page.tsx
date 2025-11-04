"use client"

import { useState } from "react"

import type React from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { useAuth } from "@/hooks/use-auth"
import { Loader2 } from "lucide-react"

export default function LoginPage() {
  const router = useRouter()
  const { login, error: authError, clearError } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    setError("")
    setIsLoading(true)

    try {
      if (!email || !password) {
        setError("Please fill in all fields")
        setIsLoading(false)
        return
      }

      await login(email, password)
      router.push("/dashboard")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed")
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="border border-white/10 bg-gradient-to-b from-white/5 to-white/0 p-8">
          {/* Header */}
          <div className="mb-8 space-y-2 text-center">
            <h1 className="text-3xl font-bold text-foreground">Welcome back</h1>
            <p className="text-muted-foreground">Sign in to your Pointer account</p>
          </div>

          {/* Error Message */}
          {(error || authError) && (
            <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-sm text-red-400">{error || authError}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email Input */}
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium text-foreground">
                Email address
              </label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-white/5 border border-white/10 text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary"
              />
            </div>

            {/* Password Input */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="text-sm font-medium text-foreground">
                  Password
                </label>
                <Link href="/forgot-password" className="text-xs text-primary hover:text-primary/80">
                  Forgot password?
                </Link>
              </div>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-white/5 border border-white/10 text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary"
              />
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-medium"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign in"
              )}
            </Button>
          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-3">
            <div className="flex-1 border-t border-white/10" />
            <span className="text-xs text-muted-foreground">or</span>
            <div className="flex-1 border-t border-white/10" />
          </div>

          {/* Sign Up Link */}
          <div className="text-center">
            <p className="text-sm text-muted-foreground">
              Don't have an account?{" "}
              <Link href="/signup" className="text-primary hover:text-primary/80 font-medium">
                Sign up
              </Link>
            </p>
          </div>
        </Card>

        {/* Footer Links */}
        <div className="mt-6 flex justify-center gap-4 text-xs text-muted-foreground">
          <Link href="/" className="hover:text-foreground">
            Back home
          </Link>
          <span>•</span>
          <Link href="/" className="hover:text-foreground">
            Terms
          </Link>
          <span>•</span>
          <Link href="/" className="hover:text-foreground">
            Privacy
          </Link>
        </div>
      </div>
    </div>
  )
}
