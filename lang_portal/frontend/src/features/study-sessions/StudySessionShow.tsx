import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { studySessionsApi } from '@/services/api'
import { StudySessionResponse } from '@/types'
import { ActivityRouter } from './ActivityRouter'

export default function StudySessionShow() {
  const { id } = useParams<{ id: string }>()
  const [session, setSession] = useState<StudySessionResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    const fetchSession = async () => {
      if (!id) return

      try {
        const response = await studySessionsApi.getById(id)
        if (mounted) {
          console.log('Received session data:', response.data)
          setSession(response.data)
        }
      } catch (error) {
        console.error('Error fetching study session:', error)
        if (mounted) {
          setError('Failed to load study session')
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    fetchSession()

    return () => {
      mounted = false
    }
  }, [id])

  if (loading) {
    return <div>Loading study session details...</div>
  }

  if (error) {
    return <div className="text-red-500">{error}</div>
  }

  if (!session) {
    return <div>Study session not found</div>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Study Session #{session.id}</h1>

      <Card>
        <CardHeader>
          <CardTitle>Session Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="font-medium">Activity Name</h3>
              <p className="text-muted-foreground">{session.activity_name || 'Not available'}</p>
            </div>
            <div>
              <h3 className="font-medium">Group Name</h3>
              <p className="text-muted-foreground">{session.group_name || 'Not available'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <ActivityRouter session={session} />
    </div>
  )
}
