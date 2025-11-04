import type React from "react"
import type { Metadata } from "next"
import { Analytics } from "@vercel/analytics/next"
import { AuthProvider } from "@/lib/auth-context"
import "./globals.css"

export const metadata: Metadata = {
  title: "Scifusion - AI-Powered Research Assistant",
  description: "Accelerate scientific discovery with AI-powered hypothesis generation and validation",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <head>
        <style>{`
html {
  --font-sans: system-ui, -apple-system, sans-serif;
  --font-mono: 'Courier New', monospace;
}
        `}</style>
      </head>
      <body>
        <AuthProvider>{children}</AuthProvider>
        <Analytics />
      </body>
    </html>
  )
}
