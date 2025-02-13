import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { studyActivitiesApi } from '@/services/api'

interface StudyActivity {
  id: string
  name: string
  thumbnail: string
  description: string
}

interface StudySession {
  id: string
  activityName: string
  groupName: string
  startTime: string
  endTime: string
  reviewItemCount: number
}

export default function StudyActivityShow() {
  const { id } = useParams<{ id: string }>()
  const [activity, setActivity] = useState<StudyActivity | null>(null)
  const [sessions, setSessions] = useState<StudySession[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchActivityData = async () => {
      if (!id) return

      try {
        const [activityRes, sessionsRes] = await Promise.all([
          studyActivitiesApi.getById(id),
          studyActivitiesApi.getStudySessions(id)
        ])

        setActivity(activityRes.data)
        setSessions(sessionsRes.data)
      } catch (error) {
        console.error('Error fetching activity data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchActivityData()
  }, [id])

  if (loading) {
    return <div>Loading activity details...</div>
  }

  if (!activity) {
    return <div>Activity not found</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">{activity.name}</h1>
        <Button asChild>
          <Link to={`/study_activities/${id}/launch`}>Launch Activity</Link>
        </Button>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="grid md:grid-cols-2 gap-6">
            <img
              src={activity.thumbnail}
              alt={activity.name}
              className="w-full h-64 object-cover rounded-lg"
            />
            <div>
              <h2 className="text-xl font-semibold mb-2">Description</h2>
              <p className="text-muted-foreground">{activity.description}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Study Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sessions.length > 0 ? (
              sessions.map((session) => (
                <div
                  key={session.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div>
                    <h3 className="font-medium">{session.groupName}</h3>
                    <p className="text-sm text-muted-foreground">
                      Started: {new Date(session.startTime).toLocaleString()}
                    </p>
                    {session.endTime && (
                      <p className="text-sm text-muted-foreground">
                        Ended: {new Date(session.endTime).toLocaleString()}
                      </p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{session.reviewItemCount} items</p>
                  </div>
                </div>
              ))
            ) : (
              <p>No study sessions found</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
