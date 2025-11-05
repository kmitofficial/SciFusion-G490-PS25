import { Card } from "@/components/ui/card"
import { ExternalLink } from "lucide-react"

interface PaperDisplayProps {
  paper: {
    title: string
    authors: string
    url: string
    abstract: string
    published_date: string
  }
}

export default function PaperDisplay({ paper }: PaperDisplayProps) {
  return (
    <Card className="bg-white/5 border-white/10 backdrop-blur p-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-lg mb-2 line-clamp-2">{paper.title}</h3>
          <p className="text-sm text-gray-400 mb-2">{paper.authors}</p>
          <p className="text-sm text-gray-300 line-clamp-3 mb-3">{paper.abstract}</p>
          <p className="text-xs text-gray-500">{paper.published_date}</p>
        </div>
        <a
          href={paper.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-shrink-0 text-white hover:text-blue-400 transition"
        >
          <ExternalLink className="w-5 h-5" />
        </a>
      </div>
    </Card>
  )
}
