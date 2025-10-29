import { LucideIcon } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'

interface DatasetCardProps {
  dataset: {
    name: string
    domain: string
    sessions: string
    events: string
    labels: string
    description: string
    icon: LucideIcon
    color: string
  }
}

const colorMap: Record<string, string> = {
  blue: 'bg-blue-500/10 text-blue-600',
  orange: 'bg-orange-500/10 text-orange-600',
  purple: 'bg-purple-500/10 text-purple-600',
}

export function DatasetCard({ dataset }: DatasetCardProps) {
  const Icon = dataset.icon
  const colorClass = colorMap[dataset.color] || colorMap.blue
  
  return (
    <Card className="group hover:shadow-lg transition-all duration-200 hover:-translate-y-1">
      <CardHeader>
        <div className={`w-12 h-12 rounded-lg ${colorClass} flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
          <Icon className="w-6 h-6" />
        </div>
        
        <CardTitle className="text-2xl">{dataset.name}</CardTitle>
        
        <Badge variant="secondary" className="w-fit">
          {dataset.domain}
        </Badge>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <CardDescription className="leading-relaxed">
          {dataset.description}
        </CardDescription>
        
        <Separator />
        
        <div className="space-y-3 text-sm">
          <div className="flex justify-between items-center">
            <span className="text-muted-foreground">Sessions/Users:</span>
            <span className="font-semibold">{dataset.sessions}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-muted-foreground">Total Events:</span>
            <span className="font-semibold">{dataset.events}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-muted-foreground">Cognitive Labels:</span>
            <span className="font-semibold">{dataset.labels}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

