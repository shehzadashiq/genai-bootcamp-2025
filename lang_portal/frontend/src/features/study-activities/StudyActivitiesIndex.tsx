import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { studyActivitiesApi } from '@/services/api'

interface StudyActivity {
  id: string
  name: string
  thumbnail: string
  description: string
}

export default function StudyActivitiesIndex() {
  const [activities, setActivities] = useState<StudyActivity[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchActivities = async () => {
      try {
        const response = await studyActivitiesApi.getAll()
        setActivities(response.data)
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
          <Card key={activity.id}>
            <CardHeader>
              <CardTitle>{activity.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <img
                src={activity.thumbnail}
                alt={activity.name}
                className="w-full h-48 object-cover rounded-md"
              />
              <p className="text-sm text-muted-foreground">{activity.description}</p>
              <div className="flex space-x-2">
                <Button asChild>
                  <Link to={`/study_activities/${activity.id}/launch`}>Launch</Link>
                </Button>
                <Button variant="outline" asChild>
                  <Link to={`/study_activities/${activity.id}`}>View Details</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
