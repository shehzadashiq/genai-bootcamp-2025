import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { studyActivitiesApi } from '@/services/api'

interface StudyActivity {
  id: number
  name: string
  description: string
  thumbnail_url: string
  url: string
}

interface PaginationInfo {
  current_page: number
  total_pages: number
  total_items: number
  items_per_page: number
}

interface StudyActivitiesResponse {
  items: StudyActivity[]
  pagination: PaginationInfo
}

export default function StudyActivitiesIndex() {
  const [activities, setActivities] = useState<StudyActivity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchActivities = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await studyActivitiesApi.getAll()
        const data = response.data
        setActivities(data.items || [])
      } catch (error) {
        console.error('Error fetching study activities:', error)
        setError('Failed to load study activities')
      } finally {
        setLoading(false)
      }
    }

    fetchActivities()
  }, [])

  if (loading) {
    return <div>Loading study activities...</div>
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-500">
        <p>{error}</p>
      </div>
    )
  }

  if (!activities || activities.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground mb-4">No study activities available</p>
        <p className="text-sm">Please check back later for new activities</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Study Activities</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {activities.map((activity) => (
          <Card 
          key={activity.id} 
          className="hover:shadow-lg transition-shadow overflow-hidden border-2 rounded-xl hover:scale-105 transform transition-transform duration-200">
          <Link to={activity.url} className="block h-full">
            <CardHeader className="pb-2">
              <CardTitle className="text-xl leading-tight">{activity.name}</CardTitle>
              </CardHeader>
              <CardContent>
              <div className="aspect-square bg-muted rounded-md mb-4 overflow-hidden flex items-center justify-center">
                  {activity.thumbnail_url && (
                    <img
                      src={activity.thumbnail_url}
                      alt={activity.name}
                      className="w-full h-full object-contain"
                    />
                  )}
                </div>
                <p className="text-muted-foreground line-clamp-2">{activity.description}</p>
              </CardContent>
            </Link>
          </Card>
        ))}
      </div>
    </div>
  )
}
