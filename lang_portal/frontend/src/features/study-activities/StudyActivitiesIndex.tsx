import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { studyActivitiesApi } from '@/services/api'

interface StudyActivity {
  id: number
  name: string
  thumbnail_url: string
  description: string
}

export default function StudyActivitiesIndex() {
  const [activities, setActivities] = useState<StudyActivity[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchActivities = async () => {
      try {
        const response = await studyActivitiesApi.getAll()
        setActivities(response.data.items || [])
      } catch (error) {
        console.error('Error fetching study activities:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchActivities()
  }, [])

  if (loading) {
    return <div>Loading study activities...</div>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Study Activities</h1>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {activities.map((activity) => (
          <Card key={activity.id} className="overflow-hidden">
            {activity.thumbnail_url && (
              <img
                src={activity.thumbnail_url}
                alt={activity.name}
                className="w-full h-48 object-cover"
              />
            )}
            <CardHeader>
              <CardTitle>{activity.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">{activity.description}</p>
              <div className="flex gap-4">
                <Link
                  to={`/study_activities/${activity.id}/launch`}
                  className="flex-1 py-2 text-center bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                >
                  Launch
                </Link>
                <Link
                  to={`/study_activities/${activity.id}`}
                  className="flex-1 py-2 text-center bg-muted text-muted-foreground rounded-md hover:bg-muted/90"
                >
                  View Details
                </Link>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {activities.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">No study activities available.</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
