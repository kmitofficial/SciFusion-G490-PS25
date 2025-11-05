import { Card } from "@/components/ui/card"
import { CheckCircle } from "lucide-react"

interface ResultDisplayProps {
  result: {
    title: string
    description: string
    metrics: Record<string, number>
    timestamp: string
  }
}

export default function ExperimentResultDisplay({ result }: ResultDisplayProps) {
  return (
    <Card className="bg-white/5 border-white/10 backdrop-blur p-6">
      <div className="flex items-start gap-4">
        <CheckCircle className="w-6 h-6 text-green-400 flex-shrink-0 mt-1" />
        <div className="flex-1">
          <h3 className="font-semibold text-lg mb-2">{result.title}</h3>
          <p className="text-gray-300 mb-4">{result.description}</p>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(result.metrics).map(([key, value]) => (
              <div key={key} className="bg-white/5 rounded p-3">
                <p className="text-xs text-gray-400 uppercase tracking-widest">{key}</p>
                <p className="text-lg font-semibold text-white">
                  {typeof value === "number" ? value.toFixed(2) : value}
                </p>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-4">{result.timestamp}</p>
        </div>
      </div>
    </Card>
  )
}
