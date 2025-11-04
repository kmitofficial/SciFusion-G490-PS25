import { generateText } from "ai"

export async function POST(request: Request) {
  try {
    const { messages } = await request.json()

    if (!messages || messages.length === 0) {
      return new Response(JSON.stringify({ error: "No messages provided" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      })
    }

    // Get the last user message
    const lastMessage = messages[messages.length - 1]

    if (lastMessage.role !== "user") {
      return new Response(JSON.stringify({ error: "Last message must be from user" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      })
    }

    const { text } = await generateText({
      model: "openai/gpt-4o-mini",
      system: `You are Scifusion, an intelligent AI assistant specialized in helping developers. You provide:
- Code reviews and suggestions
- Debugging assistance
- Performance optimization tips
- Best practices for coding and development
- Explanation of complex concepts

Be concise, practical, and helpful. Format code examples properly.`,
      messages: messages.map((msg: any) => ({
        role: msg.role,
        content: msg.content,
      })),
    })

    return new Response(JSON.stringify({ content: text }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })
  } catch (error) {
    console.error("Chat API error:", error)
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : "Failed to generate response",
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      },
    )
  }
}
