import { Card } from "@/components/ui/card"
import { Lightbulb } from "lucide-react"

interface IdeaDisplayProps {
  idea: {
    title: string
    description: string
    novelty_score: number
    potential_impact: string
  }
}

export default function IdeaDisplay({ idea }: IdeaDisplayProps) {
  return (
    <Card className="bg-white/5 border-white/10 backdrop-blur p-6">
      <div className="flex items-start gap-4">
        <Lightbulb className="w-6 h-6 text-yellow-400 flex-shrink-0 mt-1" />
        <div className="flex-1">
          <h3 className="font-semibold text-lg mb-2">{idea.title}</h3>
          <p className="text-gray-300 mb-3">{idea.description}</p>
          <div className="flex items-center gap-6 text-sm">
            <div>
              <span className="text-gray-400">Novelty Score:</span>
              <span className="ml-2 font-semibold text-blue-400">{idea.novelty_score.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-400">Potential Impact:</span>
              <span className="ml-2 font-semibold text-green-400">{idea.potential_impact}</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}
