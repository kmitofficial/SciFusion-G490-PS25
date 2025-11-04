"use client"

import { useState } from "react"

import type React from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { useAuth } from "@/hooks/use-auth"
import { Loader2, Check } from "lucide-react"

export default function SignupPage() {
  const router = useRouter()
  const { signup, error: authError, clearError } = useAuth()
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    setError("")
    setIsLoading(true)

    // Validation
    if (!formData.name || !formData.email || !formData.password || !formData.confirmPassword) {
      setError("Please fill in all fields")
      setIsLoading(false)
      return
    }

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match")
      setIsLoading(false)
      return
    }

    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters")
      setIsLoading(false)
      return
    }

    try {
      await signup(formData.name, formData.email, formData.password)
      setSuccess(true)
      setTimeout(() => {
        router.push("/chat")
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed")
      setIsLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <Card className="border border-white/10 bg-gradient-to-b from-white/5 to-white/0 p-8 text-center">
            <div className="mb-4 flex justify-center">
              <div className="rounded-full bg-primary/20 p-3">
                <Check className="h-6 w-6 text-primary" />
              </div>
            </div>
            <h2 className="mb-2 text-2xl font-bold text-foreground">Account created!</h2>
            <p className="mb-6 text-muted-foreground">Welcome to Pointer. Redirecting you to your dashboard...</p>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="border border-white/10 bg-gradient-to-b from-white/5 to-white/0 p-8">
          {/* Header */}
          <div className="mb-8 space-y-2 text-center">
            <h1 className="text-3xl font-bold text-foreground">Create account</h1>
            <p className="text-muted-foreground">Join Pointer to accelerate your development</p>
          </div>

          {/* Error Message */}
          {(error || authError) && (
            <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-sm text-red-400">{error || authError}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name Input */}
            <div className="space-y-2">
              <label htmlFor="name" className="text-sm font-medium text-foreground">
                Full name
              </label>
              <Input
                id="name"
                name="name"
                type="text"
                placeholder="John Doe"
                value={formData.name}
                onChange={handleChange}
                className="bg-white/5 border border-white/10 text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary"
              />
            </div>

            {/* Email Input */}
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium text-foreground">
                Email address
              </label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="you@example.com"
                value={formData.email}
                onChange={handleChange}
                className="bg-white/5 border border-white/10 text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary"
              />
            </div>

            {/* Password Input */}
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium text-foreground">
                Password
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={handleChange}
                className="bg-white/5 border border-white/10 text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary"
              />
            </div>

            {/* Confirm Password Input */}
            <div className="space-y-2">
              <label htmlFor="confirmPassword" className="text-sm font-medium text-foreground">
                Confirm password
              </label>
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                placeholder="••••••••"
                value={formData.confirmPassword}
                onChange={handleChange}
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
                  Creating account...
                </>
              ) : (
                "Create account"
              )}
            </Button>
          </form>

          {/* Terms */}
          <p className="mt-4 text-center text-xs text-muted-foreground">
            By signing up, you agree to our{" "}
            <Link href="/" className="text-primary hover:text-primary/80">
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link href="/" className="text-primary hover:text-primary/80">
              Privacy Policy
            </Link>
          </p>

          {/* Divider */}
          <div className="my-6 flex items-center gap-3">
            <div className="flex-1 border-t border-white/10" />
            <span className="text-xs text-muted-foreground">or</span>
            <div className="flex-1 border-t border-white/10" />
          </div>

          {/* Login Link */}
          <div className="text-center">
            <p className="text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link href="/login" className="text-primary hover:text-primary/80 font-medium">
                Sign in
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
